# Usamos una imagen base de Python
FROM python:3.9-slim

# Instalamos las dependencias necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos los archivos necesarios de tu aplicación al contenedor
COPY . /app

# Instalamos las dependencias de Python necesarias para Flask
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos los puertos en los que MariaDB y la app Flask van a escuchar
EXPOSE 5000

# Comando para iniciar la aplicación Flask
CMD python app.py
