"""
Script para ejecutar solo la API REST del Sistema YaTeApruebo.
Útil para desarrollo y testing sin Telegram.
"""

import asyncio
import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Función principal para ejecutar la API."""
    try:
        # Importar la función de la API
        from api import iniciar_api_server
        
        print("🚀 Iniciando API REST del Sistema YaTeApruebo...")
        print("📚 La documentación interactiva estará disponible en:")
        print("   - Swagger UI: http://localhost:8000/docs")
        print("   - ReDoc: http://localhost:8000/redoc")
        print("\n💡 Endpoints principales:")
        print("   - POST /evaluacion - Crear nueva evaluación")
        print("   - GET /evaluacion/{session_id}/reporte - Descargar reporte PDF")
        print("   - GET /evaluaciones - Listar todas las evaluaciones")
        print("   - GET /health - Verificar estado del sistema")
        print("\n⏹️ Presiona Ctrl+C para detener el servidor")
        
        # Iniciar servidor
        iniciar_api_server(host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\n⏹️ Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()