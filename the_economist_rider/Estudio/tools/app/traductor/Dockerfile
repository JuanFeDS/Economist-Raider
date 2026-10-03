FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Precarga el paquete de idioma en tiempo de build, para no depender de la red de Argos en cada arranque.
COPY precargar_modelo.py .
RUN python precargar_modelo.py

COPY app.py .

ENV PORT=8080
EXPOSE 8080

# --threads 1: una sola traducción a la vez por instancia (Argos/CTranslate2 no está pensado
# para llamadas concurrentes dentro del mismo proceso). Cloud Run escala con más instancias,
# no con más hilos acá. --timeout 0: una traducción larga puede tardar varios minutos.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 1 --timeout 0 app:app
