# 💾 Estrategia de Almacenamiento Escalable

Documento técnico para gestionar 100GB iniciales expandible a 1TB con máxima eficiencia.

## 📊 Análisis de Consumo

### Almacenamiento por Tipo de Contenido

```
IMÁGENES (Estimado)
├─ Tamaño promedio: 1.5 MB (comprimida)
├─ Uploads por usuario/mes: 30
├─ Almacenamiento anual: 540 MB/usuario
└─ Para 1,000 usuarios: ~540 GB/año

VIDEOS (Estimado)
├─ Tamaño por minuto: 15 MB (720p comprimido)
├─ Uploads por usuario/mes: 5 minutos
├─ Almacenamiento anual: 900 MB/usuario
└─ Para 1,000 usuarios: ~900 GB/año

TOTAL PROYECTADO
├─ 100 usuarios (6 meses): ~12 GB
├─ 500 usuarios (1 año): ~70 GB
├─ 1,000 usuarios (1 año): ~140 GB ⚠️ Requiere expansión
└─ 5,000+ usuarios: > 700 GB (Nube recomendada)
```

## 📁 Estructura de Directorios

```
backend/storage/ (100 GB - 1 TB)
├── images/
│   ├── 2026/
│   │   ├── 05/
│   │   │   ├── 16/
│   │   │   │   └── {uuid}.jpg (comprimida)
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── videos/
│   ├── 2026/
│   │   ├── 05/
│   │   │   ├── 16/
│   │   │   │   └── {uuid}.mp4 (comprimida)
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── thumbnails/
│   ├── images/
│   │   └── {uuid}_thumb.jpg (100 KB aprox)
│   └── videos/
│       └── {uuid}_thumb.jpg (100 KB aprox)
└── temp/
    └── processing/ (Archivos temporales)
```

## 🔧 Compresión Automática (Clave para Eficiencia)

### Imágenes

```javascript
// Compresión antes de guardar
const COMPRESSION_CONFIG = {
  quality: 80,           // 80% calidad = -60% tamaño
  resize: {
    width: 1920,
    height: 1080,
    fit: 'inside',
    withoutEnlargement: true
  },
  format: 'jpeg'         // JPEG más eficiente
};

// Resultado:
// Original: 5 MB → Comprimida: 1.5 MB (70% ahorro)
```

### Videos

```bash
# Compresión con FFmpeg
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -preset medium \
  -crf 23 \
  -b:v 2000k \
  -c:a aac -b:a 128k \
  output.mp4

# Resultado:
# Original: 150 MB → Comprimida: 20 MB (87% ahorro)
```

### Ahorro Total

```
Sin compresión:
├─ 1,000 usuarios × 5 MB/imagen × 360 imágenes/año = 1.8 TB
└─ 1,000 usuarios × 150 MB/video × 60 videos/año = 9 TB
Total: ~10.8 TB/año

Con compresión (80%):
├─ 1,000 usuarios × 1.5 MB/imagen × 360 = 540 GB
└─ 1,000 usuarios × 20 MB/video × 60 = 1.2 TB
Total: ~1.8 TB/año ✅ 83% MÁS EFICIENTE
```

## 🛡️ Estrategia por Fases

### FASE 1: Local en Laptop (0-500 usuarios, 6 meses)

```yaml
Hardware:
  RAM: 2-4 GB
  Disco: 100 GB local + 100 GB portátil USB 3.0
  CPU: 2+ núcleos

Config docker-compose:
  volumes:
    - ./backend/storage:/app/storage  # Local

Beneficios:
  ✅ Bajo costo
  ✅ Control total
  ✅ Desarrollo fácil
  ✅ Backup manual simple

Limitaciones:
  ❌ Depende de hardware laptop
  ❌ Sin redundancia
  ❌ Ancho de banda limitado
```

### FASE 2: Disco Portátil Externo (500-2,000 usuarios)

```yaml
Hardware:
  Disco Externo: 1 TB USB 3.0 (~$60)
  o NAS: 4 bahías con RAID 1 (~$400)

Configuración:
  # Conectar disco portátil
  mount /dev/sdb1 /mnt/external-1tb
  
  # Modificar docker-compose.yml
  volumes:
    - /mnt/external-1tb/social-storage:/app/storage

Beneficios:
  ✅ 10x más capacidad
  ✅ Transferible entre máquinas
  ✅ Bajo costo
  ✅ Fácil backup

Limitaciones:
  ❌ Velocidad USB vs SSD
  ⚠️ Requiere conexión física
```

### FASE 3: Almacenamiento en Nube (2,000+ usuarios)

```yaml
Opciones:

1. MinIO (Self-hosted S3-compatible)
   - Para tu mismo servidor
   - Control total
   - Escalable

2. AWS S3
   - $0.023/GB/mes
   - 1 TB/mes = $23
   - Infinitamente escalable

3. DigitalOcean Spaces
   - $5/mes por 250 GB
   - Similar a S3
   - Más barato

Config para S3:
  STORAGE_TYPE=s3
  AWS_ACCESS_KEY_ID=xxx
  AWS_SECRET_ACCESS_KEY=xxx
  S3_BUCKET=social-media-prod
  S3_REGION=us-east-1
```

## 🔄 Políticas de Limpieza y Retención

### Borrado de Archivos

```javascript
// Borrar archivos de posts eliminados
const CLEANUP_POLICY = {
  keepDeletedPostsFor: '30 days',   // Recuperación
  keepThumbnailsFor: '1 year',      // Rápido acceso
  keepOriginalVideosFor: '2 years', // Archivos
};

// Cron job diario
0 2 * * * node /app/src/utils/cleanup.js
```

### Compresión Retroactiva

```javascript
// Reecomprimir archivos antiguos para ahorrar espacio
const RECOMPRESS_POLICY = {
  imagesOlderThan: '3 months',
  videosOlderThan: '3 months',
  newQuality: 75,  // De 80 a 75 (aún excelente)
  estimatedSavings: '15-20%'
};
```

## 📊 Monitoreo de Uso

### Dashboard de Almacenamiento

```bash
# Ver uso total
du -sh backend/storage/

# Ver por tipo
du -sh backend/storage/images/
du -sh backend/storage/videos/
du -sh backend/storage/thumbnails/

# Ver consumo por usuario (Top 10)
find backend/storage -name "*.jpg" -o -name "*.mp4" | \
  xargs -I {} stat -c %s {} | \
  awk '{sum+=$1} END {print sum/1024/1024 " MB"}'
```

### Alertas de Espacio

```javascript
// Verificar cada hora
const checkStorageSpace = async () => {
  const usage = await getStorageUsage();
  
  if (usage.percent > 80) {
    alert('⚠️ Almacenamiento al 80% - Considerar expansión');
  }
  if (usage.percent > 95) {
    alert('🚨 CRÍTICO: Almacenamiento al 95% - Expandir INMEDIATAMENTE');
  }
};
```

## 💾 Backup y Recuperación

### Estrategia de Backup

```bash
# Backup diario a disco externo
0 3 * * * rsync -av --delete \
  /app/storage/ \
  /mnt/backup-1tb/social-media-backup/

# Backup semanal comprimido
0 4 * * 0 tar -czf \
  /mnt/backup/social-$(date +%Y%m%d).tar.gz \
  /app/storage/

# Mantener últimos 4 backups
find /mnt/backup -name "social-*.tar.gz" -mtime +28 -delete
```

### Recuperación de Desastres

```bash
# Restaurar desde backup
rsync -av --delete \
  /mnt/backup-1tb/social-media-backup/ \
  /app/storage/

# O desde tar
tar -xzf /mnt/backup/social-20260516.tar.gz -C /app/
```

## 🚀 Migración a Nube (Cuando Escales)

### Paso a Paso

```bash
# 1. Instalar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# 2. Configurar credenciales
aws configure

# 3. Crear bucket S3
aws s3 mb s3://social-media-prod-empireyoncar

# 4. Subir archivos existentes
aws s3 sync backend/storage s3://social-media-prod-empireyoncar

# 5. Actualizar backend para usar S3
# Cambiar STORAGE_TYPE=s3 en .env

# 6. Actualizar aplicación a usar SDK S3
npm install aws-sdk
```

## 📈 Proyección Financiera

### Costo Total de Almacenamiento (5 años)

```
Fase 1 (Laptop, 6 meses):
├─ Disco portátil 1TB: $60
└─ Electricidad: ~$20
Total: $80

Fase 2 (NAS, 1 año):
├─ NAS 4-bahías: $400
├─ Discos (4×2TB): $200
└─ Electricidad: $40
Total: $640

Fase 3 (AWS S3, Escalado):
├─ 1 TB/mes × 12 meses × 3.5 años: $276
└─ Transfer OUT: ~$100
Total: $376

5 AÑOS TOTAL: ~$1,096
```

## ✅ Checklist de Implementación

- [ ] Crear estructura de directorios
- [ ] Implementar compresión de imágenes con Sharp
- [ ] Implementar compresión de videos con FFmpeg
- [ ] Configurar política de limpieza automática
- [ ] Monitoreo de espacio en disco
- [ ] Backup automático diario
- [ ] Documentación de recuperación
- [ ] Probar con datos reales
- [ ] Preparar migración a S3 (código)
- [ ] Plan financiero presentado a stakeholders

---

**Resumen:** Con esta estrategia soportas 1-10k usuarios eficientemente, comenzando con 100GB en laptop y expandiendo a 1TB sin problemas. La compresión es clave: ahorra 70-80% de espacio manteniendo calidad.
