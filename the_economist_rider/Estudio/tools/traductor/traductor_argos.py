"""Traduce un archivo de texto plano usando Argos Translate (offline)."""

import argparse
import sys
from pathlib import Path

import argostranslate.package
import argostranslate.translate


def asegurar_paquete_instalado(idioma_origen, idioma_destino):
    """Descarga e instala el paquete de idioma si todavía no está disponible."""
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
        print(f"Error: no existe un paquete Argos para '{idioma_origen}' -> '{idioma_destino}'", file=sys.stderr)
        sys.exit(1)

    ruta_descarga = paquete.download()
    argostranslate.package.install_from_path(ruta_descarga)


def traducir_texto(texto, idioma_origen, idioma_destino):
    """Traduce párrafo por párrafo para conservar la estructura del archivo."""
    parrafos = texto.split("\n\n")
    parrafos_traducidos = [
        argostranslate.translate.translate(parrafo, idioma_origen, idioma_destino)
        if parrafo.strip()
        else parrafo
        for parrafo in parrafos
    ]
    return "\n\n".join(parrafos_traducidos)


def parsear_argumentos():
    """Define y parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Traduce un .txt con Argos Translate.")
    parser.add_argument("entrada", type=Path, help="Ruta del archivo de texto a traducir")
    parser.add_argument("--origen", default="en", help="Código de idioma de origen (default: en)")
    parser.add_argument("--destino", default="es", help="Código de idioma de destino (default: es)")
    parser.add_argument("--salida", type=Path, default=None, help="Ruta del archivo de salida")
    return parser.parse_args()


def main():
    """Punto de entrada del script."""
    argumentos = parsear_argumentos()

    if not argumentos.entrada.is_file():
        print(f"Error: no se encontró el archivo '{argumentos.entrada}'", file=sys.stderr)
        sys.exit(1)

    asegurar_paquete_instalado(argumentos.origen, argumentos.destino)

    texto_original = argumentos.entrada.read_text(encoding="utf-8")
    texto_traducido = traducir_texto(texto_original, argumentos.origen, argumentos.destino)

    ruta_salida = argumentos.salida or argumentos.entrada.with_stem(argumentos.entrada.stem + "_es")
    ruta_salida.write_text(texto_traducido, encoding="utf-8")
    print(f"Listo: {ruta_salida}")


if __name__ == "__main__":
    main()
