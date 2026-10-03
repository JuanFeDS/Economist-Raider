"""Convierte un PDF a texto plano (.txt) o Markdown (.md)."""

import argparse
import re
import sys
from pathlib import Path

import fitz

PATRON_GUION_DE_CORTE = re.compile(r"-$")


def unir_lineas_cortadas(texto_pagina):
    """Reconstruye párrafos uniendo líneas cortadas por el ancho de columna del PDF.

    PyMuPDF extrae el texto siguiendo los saltos de línea de la maquetación
    (columnas, justificado), que no coinciden con los saltos de oración o de
    párrafo reales. Esto rompe herramientas posteriores (como un traductor)
    que interpretan cada salto de línea como un límite de párrafo.
    """
    lineas = texto_pagina.split("\n")
    parrafos = []
    lineas_del_parrafo_actual = []

    def cerrar_parrafo():
        if lineas_del_parrafo_actual:
            parrafos.append(unir_lineas_de_un_parrafo(lineas_del_parrafo_actual))
            lineas_del_parrafo_actual.clear()

    for linea in lineas:
        linea = linea.rstrip()
        if not linea:
            cerrar_parrafo()
            continue
        lineas_del_parrafo_actual.append(linea)

    cerrar_parrafo()
    return "\n\n".join(parrafos)


def unir_lineas_de_un_parrafo(lineas):
    """Une las líneas de un párrafo, reconstruyendo palabras cortadas con guión."""
    parrafo_unido = lineas[0]
    for linea in lineas[1:]:
        if PATRON_GUION_DE_CORTE.search(parrafo_unido):
            parrafo_unido = parrafo_unido[:-1] + linea
        else:
            parrafo_unido = parrafo_unido + " " + linea
    return parrafo_unido


def extraer_paginas(ruta_pdf, limpiar_layout=True):
    """Devuelve una lista con el texto de cada página del PDF."""
    documento = fitz.open(ruta_pdf)
    paginas = [pagina.get_text().strip() for pagina in documento]
    documento.close()

    if limpiar_layout:
        paginas = [unir_lineas_cortadas(pagina) for pagina in paginas]

    return paginas


def construir_texto_plano(paginas):
    """Arma el contenido .txt separando páginas con un divisor simple."""
    separador = "\n\n" + "-" * 40 + "\n\n"
    return separador.join(paginas)


def construir_markdown(paginas, titulo):
    """Arma el contenido .md con un encabezado por página."""
    bloques = [f"# {titulo}\n"]
    for numero, texto in enumerate(paginas, start=1):
        bloques.append(f"## Página {numero}\n\n{texto}")
    return "\n\n".join(bloques)


def convertir(ruta_pdf, formato, ruta_salida, limpiar_layout=True):
    """Extrae el texto del PDF y lo guarda en el formato indicado."""
    paginas = extraer_paginas(ruta_pdf, limpiar_layout)

    if formato == "md":
        contenido = construir_markdown(paginas, ruta_pdf.stem)
    else:
        contenido = construir_texto_plano(paginas)

    ruta_salida.write_text(contenido, encoding="utf-8")


def resolver_ruta_salida(ruta_pdf, formato, ruta_salida_argumento):
    """Determina dónde guardar el resultado si no se especificó salida."""
    if ruta_salida_argumento is not None:
        return ruta_salida_argumento
    return ruta_pdf.with_suffix(f".{formato}")


def parsear_argumentos():
    """Define y parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Convierte un PDF a texto plano o Markdown.")
    parser.add_argument("pdf", type=Path, help="Ruta del archivo PDF de entrada")
    parser.add_argument(
        "--formato",
        choices=["txt", "md"],
        default="txt",
        help="Formato de salida (por defecto: txt)",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=None,
        help="Ruta del archivo de salida (por defecto: mismo nombre que el PDF)",
    )
    parser.add_argument(
        "--sin-limpiar",
        action="store_true",
        help="No reconstruir párrafos cortados por el layout del PDF (mantiene el texto línea por línea tal como lo extrae PyMuPDF)",
    )
    return parser.parse_args()


def main():
    """Punto de entrada del script."""
    argumentos = parsear_argumentos()

    if not argumentos.pdf.is_file():
        print(f"Error: no se encontró el archivo '{argumentos.pdf}'", file=sys.stderr)
        sys.exit(1)

    ruta_salida = resolver_ruta_salida(argumentos.pdf, argumentos.formato, argumentos.salida)
    convertir(argumentos.pdf, argumentos.formato, ruta_salida, limpiar_layout=not argumentos.sin_limpiar)
    print(f"Listo: {ruta_salida}")


if __name__ == "__main__":
    main()
