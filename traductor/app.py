"""Servicio de traducción: recibe un trabajo y lo procesa con Argos Translate."""

import os
from pathlib import Path

import argostranslate.package
import argostranslate.translate
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from supabase import create_client

DIRECTORIO_BASE = Path(__file__).parent
load_dotenv(DIRECTORIO_BASE.parent / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

app = Flask(__name__)


def obtener_cliente_autenticado(token):
    """Crea un cliente de Supabase que actúa en nombre del usuario dueño del trabajo."""
    cliente = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    cliente.postgrest.auth(token)
    return cliente


def asegurar_paquete_instalado(idioma_origen, idioma_destino):
    """Descarga e instala el paquete de idioma de Argos si todavía no está disponible."""
    idiomas_instalados = argostranslate.translate.get_installed_languages()
    origen = next((i for i in idiomas_instalados if i.code == idioma_origen), None)
    destino = next((i for i in idiomas_instalados if i.code == idioma_destino), None)
    if origen is not None and destino is not None and origen.get_translation(destino) is not None:
        return

    argostranslate.package.update_package_index()
    paquetes_disponibles = argostranslate.package.get_available_packages()
    paquete = next(
        (p for p in paquetes_disponibles if p.from_code == idioma_origen and p.to_code == idioma_destino),
        None,
    )
    if paquete is None:
        raise ValueError(f"No existe un paquete Argos para '{idioma_origen}' -> '{idioma_destino}'")

    argostranslate.package.install_from_path(paquete.download())
    argostranslate.translate.get_installed_languages.cache_clear()


@app.route("/traducir", methods=["POST"])
def procesar_traduccion():
    """Traduce un texto completo, actualizando el trabajo en Postgres a medida que avanza.

    Corre de forma síncrona dentro del request a propósito: en Cloud Run, fuera de un
    request activo no hay CPU garantizada, así que todo el trabajo tiene que vivir
    adentro de esta única llamada HTTP (que puede durar hasta 60 minutos).
    """
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        return jsonify(error="No autenticado"), 401
    cliente = obtener_cliente_autenticado(token)

    datos = request.get_json(force=True)
    id_trabajo = datos["id_trabajo"]
    texto = datos["texto"]
    idioma_origen = datos.get("origen", "en")
    idioma_destino = datos.get("destino", "es")
    hash_documento = datos.get("hash")

    def actualizar_trabajo(campos):
        cliente.table("trabajos_traduccion").update(campos).eq("id", id_trabajo).execute()

    def actualizar_parrafo(indice, traducido):
        cliente.table("trabajo_parrafos").update({"traducido": traducido}).eq("trabajo_id", id_trabajo).eq(
            "indice", indice
        ).execute()

    try:
        asegurar_paquete_instalado(idioma_origen, idioma_destino)
        actualizar_trabajo({"fase": "traduciendo"})

        parrafos = texto.split("\n\n")
        parrafos_con_contenido = sum(1 for p in parrafos if p.strip())

        # Se insertan todas las filas de una sola vez (un solo viaje de red, no uno por párrafo).
        cliente.table("trabajo_parrafos").insert(
            [{"trabajo_id": id_trabajo, "indice": i, "original": p} for i, p in enumerate(parrafos)]
        ).execute()
        actualizar_trabajo({"total_parrafos": parrafos_con_contenido})

        parrafos_procesados = 0
        traducciones = []
        for indice, parrafo in enumerate(parrafos):
            if parrafo.strip():
                traducido = argostranslate.translate.translate(parrafo, idioma_origen, idioma_destino)
                parrafos_procesados += 1
            else:
                traducido = parrafo
            traducciones.append(traducido)

            # Cada actualización toca solo la fila de este párrafo: no reenvía los anteriores.
            actualizar_parrafo(indice, traducido)
            actualizar_trabajo({
                "parrafo_actual": parrafos_procesados,
                "progreso": parrafos_procesados / parrafos_con_contenido,
            })

        resultado = "\n\n".join(traducciones)
        actualizar_trabajo({"estado": "listo", "fase": "listo", "progreso": 1.0, "resultado": resultado})

        if hash_documento:
            cliente.table("documentos").update({"texto_es": resultado}).eq("hash", hash_documento).execute()
    except Exception as error:  # boundary: quien llama solo consulta el estado en la base
        actualizar_trabajo({"estado": "error", "mensaje": str(error)})

    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(port=5051, debug=False)
