"""Traduce un archivo de texto plano usando un modelo Helsinki-NLP (MarianMT)."""

import argparse
import sys
from pathlib import Path

from transformers import MarianMTModel, MarianTokenizer

MODELOS_POR_PAR_DE_IDIOMAS = {
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
}


def obtener_nombre_modelo(idioma_origen, idioma_destino):
    """Busca el modelo Helsinki-NLP correspondiente al par de idiomas pedido."""
    nombre_modelo = MODELOS_POR_PAR_DE_IDIOMAS.get((idioma_origen, idioma_destino))
    if nombre_modelo is None:
        print(
            f"Error: no hay un modelo configurado para '{idioma_origen}' -> '{idioma_destino}'",
            file=sys.stderr,
        )
        sys.exit(1)
    return nombre_modelo


def cargar_modelo(nombre_modelo):
    """Descarga (la primera vez) y carga el tokenizador y el modelo."""
    tokenizador = MarianTokenizer.from_pretrained(nombre_modelo)
    modelo = MarianMTModel.from_pretrained(nombre_modelo)
    return tokenizador, modelo


def traducir_parrafo(parrafo, tokenizador, modelo):
    """Traduce un párrafo completo respetando el límite de tokens del modelo."""
    entradas = tokenizador(parrafo, return_tensors="pt", padding=True, truncation=True)
    salida = modelo.generate(**entradas, max_new_tokens=512)
    return tokenizador.decode(salida[0], skip_special_tokens=True)


def traducir_texto(texto, tokenizador, modelo):
    """Traduce párrafo por párrafo para conservar la estructura del archivo."""
    parrafos = texto.split("\n\n")
    parrafos_traducidos = [
        traducir_parrafo(parrafo, tokenizador, modelo) if parrafo.strip() else parrafo
        for parrafo in parrafos
    ]
    return "\n\n".join(parrafos_traducidos)


def parsear_argumentos():
    """Define y parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Traduce un .txt con un modelo Helsinki-NLP.")
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

    nombre_modelo = obtener_nombre_modelo(argumentos.origen, argumentos.destino)
    tokenizador, modelo = cargar_modelo(nombre_modelo)

    texto_original = argumentos.entrada.read_text(encoding="utf-8")
    texto_traducido = traducir_texto(texto_original, tokenizador, modelo)

    ruta_salida = argumentos.salida or argumentos.entrada.with_stem(argumentos.entrada.stem + "_es")
    ruta_salida.write_text(texto_traducido, encoding="utf-8")
    print(f"Listo: {ruta_salida}")


if __name__ == "__main__":
    main()
