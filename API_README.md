# 🏦 Sistema YaTeApruebo - API REST

## 📋 Descripción
API REST del Sistema YaTeApruebo para evaluación inteligente de estados financieros. Permite integrar el sistema con aplicaciones externas sin necesidad de usar Telegram.

## 🚀 Inicio Rápido

### 1. Instalación
```bash
python install.py
```

### 2. Configuración
Asegúrate de que tu archivo `.env` tenga al menos:
```env
OPENAI_API_KEY_AGENT1=tu_clave_secretaria
OPENAI_API_KEY_AGENT2=tu_clave_analista
```

### 3. Ejecutar API
```bash
python run_api.py
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación

### Swagger UI (Interactiva)
`http://localhost:8000/docs`

### ReDoc
`http://localhost:8000/redoc`

## 🛠️ Endpoints Principales

### 1. Crear Evaluación
**POST** `/evaluacion`

Crea una nueva evaluación financiera.

**Parámetros:**
- `nombre_empresa` (form): Nombre de la empresa
- `sector_empresa` (form): Sector de la empresa  
- `archivo_pdf` (file): Archivo PDF del estado financiero

**Ejemplo con curl:**
```bash
curl -X POST "http://localhost:8000/evaluacion" \
  -F "nombre_empresa=Empresa ABC" \
  -F "sector_empresa=Tecnología" \
  -F "archivo_pdf=@estado_financiero.pdf"
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "session_id": "abc12345",
  "empresa": {
    "nombre": "Empresa ABC",
    "sector": "Tecnología"
  },
  "calificacion_riesgo": {
    "nivel": "BÁSICO",
    "puntuacion": 85
  },
  "pdf_path": "/ruta/al/reporte.pdf",
  "resumen": "Resumen ejecutivo del análisis..."
}
```

### 2. Descargar Reporte
**GET** `/evaluacion/{session_id}/reporte`

Descarga el reporte PDF generado.

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/evaluacion/abc12345/reporte" \
  --output reporte.pdf
```

### 3. Obtener Detalles Completos
**GET** `/evaluacion/{session_id}/detalle`

Obtiene el análisis completo en formato JSON.

**Respuesta:**
```json
{
  "session_id": "abc12345",
  "empresa": {...},
  "analisis_completo": {
    "calificacion_riesgo": {...},
    "analisis_liquidez": {...},
    "analisis_solvencia": {...},
    "analisis_rentabilidad": {...},
    "recomendaciones": [...]
  },
  "fecha_analisis": "2024-01-15T10:30:00"
}
```

### 4. Listar Evaluaciones
**GET** `/evaluaciones`

Lista todas las evaluaciones realizadas.

**Respuesta:**
```json
{
  "total": 5,
  "evaluaciones": [
    {
      "session_id": "abc12345",
      "empresa": "Empresa ABC",
      "sector": "Tecnología",
      "fecha_analisis": "2024-01-15T10:30:00",
      "calificacion_riesgo": "BÁSICO",
      "puntuacion": 85
    }
  ]
}
```

### 5. Verificar Estado
**GET** `/health`

Verifica el estado del sistema.

**Respuesta:**
```json
{
  "status": "healthy",
  "sistema_iniciado": true,
  "estadisticas": {
    "total_evaluaciones": 5,
    "evaluaciones_por_nivel": {
      "BÁSICO": 2,
      "INTERMEDIO": 2,
      "AVANZADO": 1
    }
  }
}
```

### 6. Eliminar Evaluación
**DELETE** `/evaluacion/{session_id}`

Elimina una evaluación y sus archivos asociados.

**Respuesta:**
```json
{
  "mensaje": "Evaluación eliminada exitosamente",
  "archivos_eliminados": [
    "/ruta/archivo1.json",
    "/ruta/archivo2.pdf"
  ]
}
```

## 📊 Códigos de Estado

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 400 | Error en los datos enviados |
| 404 | Recurso no encontrado |
| 500 | Error interno del servidor |
| 503 | Servicio no disponible |

## 🔒 Configuración de Seguridad

### CORS
Por defecto, la API acepta requests desde cualquier origen. Para producción, modifica `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-dominio.com"],  # Especificar dominios
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

### Límites de Archivo
- Tamaño máximo: Configurado en `settings.MAX_FILE_SIZE`
- Formatos soportados: Solo PDF

## 🧪 Testing

### Prueba Básica
```bash
# Verificar que la API esté funcionando
curl http://localhost:8000/health
```

### Prueba con Archivo
```bash
# Crear evaluación de prueba
curl -X POST "http://localhost:8000/evaluacion" \
  -F "nombre_empresa=Test Company" \
  -F "sector_empresa=Test Sector" \
  -F "archivo_pdf=@test_financial_statement.pdf"
```

## 📁 Estructura de Archivos

```
output/
├── {session_id}_analisis_completo.json  # Análisis detallado
├── Reporte_Financiero_{empresa}_{fecha}.pdf  # Reporte final
└── logs/
    └── yateapruebo.log  # Logs del sistema
```

## 🐛 Solución de Problemas

### Error 503 - Servicio no disponible
- Verificar que las claves de OpenAI estén configuradas
- Revisar logs en `output/logs/yateapruebo.log`

### Error 400 - Archivo muy grande
- Verificar tamaño del PDF (límite en settings)
- Usar herramientas de compresión PDF

### Error 500 - Error interno
- Revisar logs detallados
- Verificar que todas las dependencias estén instaladas

## 🔧 Configuración Avanzada

### Variables de Entorno
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# File Limits
MAX_FILE_SIZE=10485760  # 10MB en bytes

# OpenAI Configuration
OPENAI_API_KEY_AGENT1=sk-...
OPENAI_API_KEY_AGENT2=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

### Ejecutar en Puerto Personalizado
```bash
# Modificar run_api.py o usar variables de entorno
python -c "from api import iniciar_api_server; iniciar_api_server(port=8080)"
```

## 📈 Monitoreo

### Logs
Los logs se guardan automáticamente en:
- `output/logs/yateapruebo.log`
- Rotación automática por tamaño
- Niveles: DEBUG, INFO, WARNING, ERROR

### Métricas
Endpoint `/estadisticas` proporciona:
- Total de evaluaciones
- Distribución por nivel de riesgo
- Estado de servicios

## 🤝 Integración

### Python
```python
import requests

# Crear evaluación
with open('estado_financiero.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/evaluacion',
        data={
            'nombre_empresa': 'Mi Empresa',
            'sector_empresa': 'Tecnología'
        },
        files={'archivo_pdf': f}
    )

result = response.json()
session_id = result['session_id']

# Descargar reporte
reporte = requests.get(f'http://localhost:8000/evaluacion/{session_id}/reporte')
with open('reporte.pdf', 'wb') as f:
    f.write(reporte.content)
```

### JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');
const fetch = require('node-fetch');

async function crearEvaluacion() {
    const form = new FormData();
    form.append('nombre_empresa', 'Mi Empresa');
    form.append('sector_empresa', 'Tecnología');
    form.append('archivo_pdf', fs.createReadStream('estado_financiero.pdf'));
    
    const response = await fetch('http://localhost:8000/evaluacion', {
        method: 'POST',
        body: form
    });
    
    return await response.json();
}
```

---

**📞 Soporte:** Para dudas o problemas, revisar los logs o contactar al equipo de desarrollo.