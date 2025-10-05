# YaTeApruebo - Sistema de Análisis Financiero

Sistema de evaluación inteligente de estados financieros que utiliza dos agentes de IA especializados para automatizar el proceso de análisis de riesgo financiero.

## 🚀 Características Principales

- **Agente 1 - Secretaria Virtual**: Recopila información de la empresa y procesa documentos PDF
- **Agente 2 - Analista de Riesgos Senior**: Realiza análisis exhaustivo de estados financieros
- **Integración con Telegram**: Interfaz de usuario amigable vía bot de Telegram
- **Almacenamiento Local**: Gestión de archivos con preparación para Supabase
- **Reportes Automatizados**: Generación de informes PDF con calificaciones de riesgo

## 📋 Requisitos

- Python 3.8+
- OpenAI API Key
- Telegram Bot Token
- Acceso a Supabase (configuración futura)

## 🛠️ Instalación

1. Clona el repositorio
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Configura las variables de entorno en `.env`
4. Ejecuta el sistema:
   ```bash
   python main.py
   ```

## 📁 Estructura del Proyecto

```
YaTeApruebo/
├── agents/
│   ├── __init__.py
│   ├── secretaria_virtual.py    # Agente 1
│   └── analista_riesgos.py      # Agente 2
├── services/
│   ├── __init__.py
│   ├── telegram_service.py      # Integración Telegram
│   ├── openai_service.py        # Conexión OpenAI
│   └── file_service.py          # Gestión de archivos
├── utils/
│   ├── __init__.py
│   ├── pdf_processor.py         # Procesamiento PDF
│   ├── report_generator.py      # Generación reportes
│   └── validators.py            # Validaciones
├── data/
│   ├── input/                   # PDFs de entrada
│   ├── output/                  # Reportes generados
│   └── logs/                    # Logs del sistema
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuraciones
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias
└── .env.example                 # Ejemplo de variables
```

## 🔧 Configuración

Copia `.env.example` a `.env` y configura tus variables:

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
OPENAI_API_KEY_AGENTE1=tu_api_key_agente1
OPENAI_SEGUNDO_AGENTE=tu_api_key_agente2
```

## 🎯 Flujo de Trabajo

1. **Inicio**: Usuario inicia conversación con bot de Telegram
2. **Recopilación**: Agente 1 solicita datos de empresa y PDF
3. **Procesamiento**: Sistema almacena información y prepara análisis
4. **Análisis**: Agente 2 evalúa el estado financiero
5. **Reporte**: Generación automática de informe con calificación
6. **Entrega**: Envío del reporte al usuario vía Telegram

## 📊 Niveles de Riesgo

- **Nivel Básico**: Riesgo bajo, aprobación automática posible
- **Nivel Intermedio**: Riesgo moderado, requiere revisión
- **Nivel Avanzado**: Riesgo alto, requiere análisis especializado

## 🔮 Próximas Características

- [ ] Integración completa con Supabase
- [ ] Dashboard web para administración
- [ ] API REST para integraciones
- [ ] Análisis histórico de tendencias
- [ ] Notificaciones automáticas

## 📝 Licencia

Proyecto privado - Todos los derechos reservados

## 🤝 Contribución

Este es un proyecto interno. Para contribuir, contacta al equipo de desarrollo.