"""Servidor web: extracción de PDF, biblioteca, subrayados y notas.

La traducción en sí la hace el servicio aparte en ../traductor/app.py — este servicio solo
crea el trabajo en la base y le avisa, para no cargar PyTorch acá.
"""

import hashlib
import json
import os
import re
import threading
from datetime import datetime
from functools import wraps
from pathlib import Path

import fitz
import requests
from dotenv import load_dotenv
from flask import Flask, Response, g, jsonify, request, send_from_directory
from supabase import create_client

DIRECTORIO_BASE = Path(__file__).parent
load_dotenv(DIRECTORIO_BASE.parent / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
URL_SERVICIO_TRADUCTOR = os.environ.get("URL_SERVICIO_TRADUCTOR", "http://127.0.0.1:5051")

# En Cloud Run (GOOGLE_CLOUD_PROJECT seteado) se encola vía Cloud Tasks, porque fuera de un
# request activo Cloud Run no garantiza CPU para un hilo en segundo plano. En local, sin eso
# configurado, se dispara con un hilo simple como antes.
PROYECTO_GCP = os.environ.get("GOOGLE_CLOUD_PROJECT")
REGION_CLOUD_TASKS = os.environ.get("CLOUD_TASKS_REGION", "us-central1")
COLA_CLOUD_TASKS = os.environ.get("CLOUD_TASKS_COLA", "traduccion-queue")

PATRON_GUION_DE_CORTE = re.compile(r"-$")
ETIQUETAS_IDIOMA = {"en": "inglés", "es": "español"}

app = Flask(__name__, static_folder=str(DIRECTORIO_BASE / "static"), static_url_path="")


def obtener_cliente_autenticado():
    """Crea un cliente de Supabase que actúa en nombre del usuario autenticado (respeta RLS)."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        return None
    cliente = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    cliente.postgrest.auth(token)
    return cliente


def requiere_autenticacion(vista):
    """Exige un token válido de Supabase y lo deja disponible en g.supabase / g.token."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return jsonify(error="No autenticado"), 401
        cliente = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        cliente.postgrest.auth(token)
        g.supabase = cliente
        g.token = token
        return vista(*args, **kwargs)

    return envoltura


def unir_lineas_de_un_parrafo(lineas):
    """Une las líneas de un párrafo, reconstruyendo palabras cortadas con guión."""
    parrafo_unido = lineas[0]
    for linea in lineas[1:]:
        if PATRON_GUION_DE_CORTE.search(parrafo_unido):
            parrafo_unido = parrafo_unido[:-1] + linea
        else:
            parrafo_unido = parrafo_unido + " " + linea
    return parrafo_unido


def unir_lineas_cortadas(texto_pagina):
    """Reconstruye párrafos uniendo líneas cortadas por el ancho de columna del PDF."""
    lineas_del_parrafo_actual = []
    parrafos = []

    def cerrar_parrafo():
        if lineas_del_parrafo_actual:
            parrafos.append(unir_lineas_de_un_parrafo(lineas_del_parrafo_actual))
            lineas_del_parrafo_actual.clear()

    for linea in texto_pagina.split("\n"):
        linea = linea.rstrip()
        if not linea:
            cerrar_parrafo()
            continue
        lineas_del_parrafo_actual.append(linea)

    cerrar_parrafo()
    return "\n\n".join(parrafos)


def extraer_texto_de_pdf(datos_pdf):
    """Extrae y limpia el texto de un PDF recibido como bytes en memoria."""
    documento = fitz.open(stream=datos_pdf, filetype="pdf")
    paginas = [unir_lineas_cortadas(pagina.get_text().strip()) for pagina in documento]
    documento.close()
    return "\n\n".join(paginas)


@app.route("/")
def index():
    """Sirve la página del visor."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/extraer", methods=["POST"])
@requiere_autenticacion
def extraer():
    """Recibe un PDF y devuelve su texto ya limpio, usando la caché si ya se procesó antes."""
    archivo = request.files.get("pdf")
    if archivo is None:
        return jsonify(error="No se recibió ningún archivo"), 400

    datos_pdf = archivo.read()
    hash_documento = hashlib.sha256(datos_pdf).hexdigest()

    existente = (
        g.supabase.table("documentos")
        .select("texto_en, texto_es, posicion_en, posicion_es")
        .eq("hash", hash_documento)
        .maybe_single()
        .execute()
    )

    if existente is not None and existente.data is not None:
        fila = existente.data
        return jsonify(
            hash=hash_documento,
            texto=fila["texto_en"],
            texto_es=fila["texto_es"],
            posicion_en=fila["posicion_en"],
            posicion_es=fila["posicion_es"],
            nombre=archivo.filename,
        )

    texto = extraer_texto_de_pdf(datos_pdf)
    g.supabase.table("documentos").insert(
        {"hash": hash_documento, "nombre_archivo": archivo.filename, "texto_en": texto}
    ).execute()

    return jsonify(
        hash=hash_documento, texto=texto, texto_es=None, posicion_en=0, posicion_es=0, nombre=archivo.filename
    )


def _disparar_con_cloud_tasks(id_trabajo, texto, idioma_origen, idioma_destino, hash_documento, token):
    """Encola la traducción en Cloud Tasks, que la invoca como un request HTTP aparte y

    con reintentos. Se usa en Cloud Run porque fuera de un request activo no hay CPU
    garantizada para seguir un hilo en segundo plano.
    """
    from google.cloud import tasks_v2

    cliente_tareas = tasks_v2.CloudTasksClient()
    padre = cliente_tareas.queue_path(PROYECTO_GCP, REGION_CLOUD_TASKS, COLA_CLOUD_TASKS)

    cuerpo = json.dumps(
        {
            "id_trabajo": id_trabajo,
            "texto": texto,
            "origen": idioma_origen,
            "destino": idioma_destino,
            "hash": hash_documento,
        }
    ).encode()

    tarea = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{URL_SERVICIO_TRADUCTOR}/traducir",
            "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            "body": cuerpo,
        }
    }
    cliente_tareas.create_task(request={"parent": padre, "task": tarea})


def _disparar_con_hilo_local(id_trabajo, texto, idioma_origen, idioma_destino, hash_documento, token):
    """Llama al traductor en un hilo de fondo. Sirve para desarrollo local; en Cloud Run no
    es confiable porque el proceso puede quedarse sin CPU apenas se responde el request.
    """

    def _en_hilo():
        try:
            requests.post(
                f"{URL_SERVICIO_TRADUCTOR}/traducir",
                json={
                    "id_trabajo": id_trabajo,
                    "texto": texto,
                    "origen": idioma_origen,
                    "destino": idioma_destino,
                    "hash": hash_documento,
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=3600,
            )
        except requests.RequestException:
            pass  # el trabajo queda "procesando" en la base; el usuario puede reintentar

    threading.Thread(target=_en_hilo, daemon=True).start()


def disparar_traduccion(id_trabajo, texto, idioma_origen, idioma_destino, hash_documento, token):
    """Le avisa al servicio de traducción que hay un trabajo nuevo, sin bloquear la respuesta."""
    if PROYECTO_GCP:
        _disparar_con_cloud_tasks(id_trabajo, texto, idioma_origen, idioma_destino, hash_documento, token)
    else:
        _disparar_con_hilo_local(id_trabajo, texto, idioma_origen, idioma_destino, hash_documento, token)


@app.route("/api/traducir", methods=["POST"])
@requiere_autenticacion
def iniciar_traduccion():
    """Crea el trabajo en la base y le avisa al servicio de traducción, sin esperar a que termine.

    Si el documento ya tiene traducción guardada (mismo hash), la devuelve directo sin traducir de nuevo.
    """
    datos = request.get_json(force=True)
    texto = datos.get("texto", "")
    hash_documento = datos.get("hash")
    idioma_origen = datos.get("origen", "en")
    idioma_destino = datos.get("destino", "es")
    if not texto.strip():
        return jsonify(error="El texto a traducir está vacío"), 400

    if hash_documento:
        existente = (
            g.supabase.table("documentos").select("texto_es").eq("hash", hash_documento).maybe_single().execute()
        )
        if existente is not None and existente.data and existente.data.get("texto_es"):
            fila_trabajo = (
                g.supabase.table("trabajos_traduccion")
                .insert(
                    {
                        "hash_documento": hash_documento,
                        "estado": "listo",
                        "fase": "listo",
                        "progreso": 1.0,
                        "resultado": existente.data["texto_es"],
                    }
                )
                .execute()
            )
            return jsonify(id_trabajo=fila_trabajo.data[0]["id"])

    fila_trabajo = (
        g.supabase.table("trabajos_traduccion")
        .insert(
            {
                "hash_documento": hash_documento,
                "idioma_origen": idioma_origen,
                "idioma_destino": idioma_destino,
                "estado": "procesando",
                "fase": "iniciando",
                "progreso": 0.0,
            }
        )
        .execute()
    )
    id_trabajo = fila_trabajo.data[0]["id"]
    token = g.token  # capturado acá: fuera del contexto de request ya no existe g

    disparar_traduccion(id_trabajo, texto, idioma_origen, idioma_destino, hash_documento, token)

    return jsonify(id_trabajo=id_trabajo)


@app.route("/api/traducir/<id_trabajo>")
@requiere_autenticacion
def estado_traduccion(id_trabajo):
    """Devuelve el estado actual de un trabajo de traducción, leído de la base."""
    respuesta = (
        g.supabase.table("trabajos_traduccion").select("*").eq("id", id_trabajo).maybe_single().execute()
    )
    if respuesta is None or respuesta.data is None:
        return jsonify(error="Trabajo no encontrado"), 404

    trabajo = respuesta.data
    parrafos = (
        g.supabase.table("trabajo_parrafos")
        .select("indice, original, traducido")
        .eq("trabajo_id", id_trabajo)
        .order("indice")
        .execute()
    )
    if parrafos.data:
        trabajo["parrafos"] = [{"original": p["original"], "traducido": p["traducido"]} for p in parrafos.data]

    return jsonify(trabajo)


@app.route("/api/documentos/<hash_documento>/trabajo-activo")
@requiere_autenticacion
def obtener_trabajo_activo(hash_documento):
    """Devuelve el id del trabajo de traducción en curso para este documento, si hay uno.

    Existe para que al reabrir un documento (ej. tras recargar la página) la app se
    reconecte a una traducción que ya está corriendo del lado del servidor, en vez de
    dejar arrancar una segunda en paralelo.
    """
    respuesta = (
        g.supabase.table("trabajos_traduccion")
        .select("id")
        .eq("hash_documento", hash_documento)
        .eq("estado", "procesando")
        .order("creado_en", desc=True)
        .limit(1)
        .execute()
    )
    if respuesta.data:
        return jsonify(id_trabajo=respuesta.data[0]["id"])
    return jsonify(id_trabajo=None)


@app.route("/api/documentos")
@requiere_autenticacion
def listar_documentos():
    """Lista los documentos ya procesados, para la biblioteca lateral."""
    respuesta = (
        g.supabase.table("documentos")
        .select("hash, nombre_archivo, categoria, texto_es, creado_en")
        .order("creado_en", desc=True)
        .execute()
    )
    documentos = [
        {
            "hash": fila["hash"],
            "nombre_archivo": fila["nombre_archivo"],
            "categoria": fila["categoria"],
            "tiene_traduccion": fila["texto_es"] is not None,
            "creado_en": fila["creado_en"],
        }
        for fila in respuesta.data
    ]
    return jsonify(documentos)


@app.route("/api/documentos/<hash_documento>")
@requiere_autenticacion
def obtener_documento(hash_documento):
    """Devuelve un documento completo (textos y posición de lectura) para abrirlo desde la biblioteca."""
    respuesta = (
        g.supabase.table("documentos")
        .select("hash, nombre_archivo, texto_en, texto_es, posicion_en, posicion_es, categoria")
        .eq("hash", hash_documento)
        .maybe_single()
        .execute()
    )
    if respuesta is None or respuesta.data is None:
        return jsonify(error="Documento no encontrado"), 404
    return jsonify(respuesta.data)


@app.route("/api/documentos/<hash_documento>/posicion", methods=["POST"])
@requiere_autenticacion
def guardar_posicion(hash_documento):
    """Guarda el índice de párrafo donde el usuario dejó la lectura, por idioma."""
    datos = request.get_json(force=True)
    idioma = datos.get("idioma")
    indice_parrafo = datos.get("indice_parrafo", 0)
    if idioma not in ("en", "es"):
        return jsonify(error="Idioma inválido"), 400

    columna = "posicion_en" if idioma == "en" else "posicion_es"
    g.supabase.table("documentos").update({columna: indice_parrafo}).eq("hash", hash_documento).execute()
    return jsonify(ok=True)


@app.route("/api/documentos/<hash_documento>/nombre", methods=["POST"])
@requiere_autenticacion
def renombrar_documento(hash_documento):
    """Cambia el nombre visible de un documento."""
    datos = request.get_json(force=True)
    nombre = datos.get("nombre", "").strip()
    if not nombre:
        return jsonify(error="El nombre no puede estar vacío"), 400

    g.supabase.table("documentos").update({"nombre_archivo": nombre}).eq("hash", hash_documento).execute()
    return jsonify(ok=True)


@app.route("/api/documentos/<hash_documento>/categoria", methods=["POST"])
@requiere_autenticacion
def cambiar_categoria(hash_documento):
    """Mueve un documento a otra categoría (se crea implícitamente si no existía)."""
    datos = request.get_json(force=True)
    categoria = datos.get("categoria", "").strip() or "Sin categoría"

    g.supabase.table("documentos").update({"categoria": categoria}).eq("hash", hash_documento).execute()
    return jsonify(ok=True)


@app.route("/api/documentos/<hash_documento>", methods=["DELETE"])
@requiere_autenticacion
def eliminar_documento(hash_documento):
    """Elimina un documento de la biblioteca (texto extraído, traducción y subrayados incluidos)."""
    g.supabase.table("documentos").delete().eq("hash", hash_documento).execute()
    return jsonify(ok=True)


@app.route("/api/documentos/<hash_documento>/subrayados")
@requiere_autenticacion
def listar_subrayados(hash_documento):
    """Lista los subrayados de un documento en un idioma dado."""
    idioma = request.args.get("idioma", "en")
    respuesta = (
        g.supabase.table("subrayados")
        .select("id, parrafo_indice, offset_inicio, offset_fin, texto, comentario")
        .eq("hash_documento", hash_documento)
        .eq("idioma", idioma)
        .order("parrafo_indice")
        .order("offset_inicio")
        .execute()
    )
    return jsonify(respuesta.data)


def _hay_solapamiento(cliente_supabase, hash_documento, idioma, parrafo_indice, offset_inicio, offset_fin):
    """Verifica si un rango nuevo se superpone con un subrayado ya guardado en el mismo párrafo."""
    respuesta = (
        cliente_supabase.table("subrayados")
        .select("offset_inicio, offset_fin")
        .eq("hash_documento", hash_documento)
        .eq("idioma", idioma)
        .eq("parrafo_indice", parrafo_indice)
        .execute()
    )
    return any(offset_inicio < fila["offset_fin"] and offset_fin > fila["offset_inicio"] for fila in respuesta.data)


@app.route("/api/documentos/<hash_documento>/subrayados", methods=["POST"])
@requiere_autenticacion
def crear_subrayados(hash_documento):
    """Crea uno o más subrayados (una selección puede cruzar varios párrafos)."""
    datos = request.get_json(force=True)
    idioma = datos.get("idioma", "en")
    segmentos = datos.get("segmentos", [])

    creados = []
    for segmento in segmentos:
        parrafo_indice = segmento["parrafo_indice"]
        offset_inicio = segmento["offset_inicio"]
        offset_fin = segmento["offset_fin"]
        texto = segmento["texto"]

        if _hay_solapamiento(g.supabase, hash_documento, idioma, parrafo_indice, offset_inicio, offset_fin):
            continue

        respuesta = (
            g.supabase.table("subrayados")
            .insert(
                {
                    "hash_documento": hash_documento,
                    "idioma": idioma,
                    "parrafo_indice": parrafo_indice,
                    "offset_inicio": offset_inicio,
                    "offset_fin": offset_fin,
                    "texto": texto,
                }
            )
            .execute()
        )
        creados.append(respuesta.data[0])

    return jsonify(creados)


@app.route("/api/subrayados/<int:id_subrayado>/comentario", methods=["POST"])
@requiere_autenticacion
def guardar_comentario(id_subrayado):
    """Guarda o borra el comentario asociado a un subrayado."""
    datos = request.get_json(force=True)
    comentario = datos.get("comentario", "").strip() or None
    g.supabase.table("subrayados").update({"comentario": comentario}).eq("id", id_subrayado).execute()
    return jsonify(ok=True)


@app.route("/api/subrayados/<int:id_subrayado>", methods=["DELETE"])
@requiere_autenticacion
def eliminar_subrayado(id_subrayado):
    """Elimina un subrayado."""
    g.supabase.table("subrayados").delete().eq("id", id_subrayado).execute()
    return jsonify(ok=True)


def sanear_nombre_archivo(nombre):
    """Convierte el nombre de un documento en un nombre de archivo seguro."""
    limpio = re.sub(r"[^\w\s-]", "", nombre, flags=re.UNICODE).strip()
    return re.sub(r"[-\s]+", "-", limpio)


def construir_markdown_exportacion(nombre_documento, subrayados_por_idioma):
    """Arma el contenido Markdown con los subrayados y comentarios de un documento."""
    bloques = [
        f"# 📖 {nombre_documento}",
        "",
        f"**Exportado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    for idioma, subrayados in subrayados_por_idioma.items():
        if not subrayados:
            continue
        bloques.append(f"## ✏️ Subrayados · {ETIQUETAS_IDIOMA.get(idioma, idioma)}")
        bloques.append("")
        for subrayado in subrayados:
            bloques.append(f"> {subrayado['texto']}")
            bloques.append(f"> — párrafo {subrayado['parrafo_indice']}")
            if subrayado["comentario"]:
                bloques.append("")
                bloques.append(f"💬 {subrayado['comentario']}")
            bloques.append("")

    return "\n".join(bloques)


@app.route("/api/documentos/<hash_documento>/exportar", methods=["POST"])
@requiere_autenticacion
def exportar_notas(hash_documento):
    """Arma el .md con los subrayados y comentarios de un documento y lo devuelve como descarga."""
    documento = (
        g.supabase.table("documentos").select("nombre_archivo").eq("hash", hash_documento).maybe_single().execute()
    )
    if documento is None or documento.data is None:
        return jsonify(error="Documento no encontrado"), 404

    subrayados_por_idioma = {}
    for idioma in ("en", "es"):
        respuesta = (
            g.supabase.table("subrayados")
            .select("parrafo_indice, texto, comentario")
            .eq("hash_documento", hash_documento)
            .eq("idioma", idioma)
            .order("parrafo_indice")
            .order("offset_inicio")
            .execute()
        )
        subrayados_por_idioma[idioma] = respuesta.data

    if not any(subrayados_por_idioma.values()):
        return jsonify(error="Este documento todavía no tiene subrayados para exportar"), 400

    nombre_documento = documento.data["nombre_archivo"].rsplit(".", 1)[0]
    contenido = construir_markdown_exportacion(nombre_documento, subrayados_por_idioma)
    nombre_archivo_salida = f"{sanear_nombre_archivo(nombre_documento)}-notas.md"

    return Response(
        contenido,
        mimetype="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo_salida}"'},
    )


if __name__ == "__main__":
    app.run(port=5050, debug=False)
