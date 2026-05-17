FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY backend/modulo-autenticacion/requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY backend/modulo-autenticacion/ .

# Crear directorio para uploads
RUN mkdir -p /app/uploads/profiles /app/uploads/posts /app/uploads/groups

# Exponer puerto
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "run.py"]
