"""Descarga e instala el paquete de idioma en->es durante el build de la imagen.

Evita depender de la red externa de Argos en cada arranque del contenedor. El paquete de
traducción en sí no incluye los modelos de Stanza que usa para separar oraciones — esos se
descargan aparte, de forma perezosa, en el primer uso real. Por eso acá se fuerza una
traducción de prueba: así esa descarga también queda resuelta en el build, no en producción
(donde una descarga cortada deja un archivo corrupto y todo falla con un error de MD5).
"""

import argostranslate.package
import argostranslate.translate

argostranslate.package.update_package_index()
paquete = next(
    p for p in argostranslate.package.get_available_packages() if p.from_code == "en" and p.to_code == "es"
)
argostranslate.package.install_from_path(paquete.download())

argostranslate.translate.translate("This is a warm-up sentence.", "en", "es")
