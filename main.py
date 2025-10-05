"""
Sistema YaTeApruebo - Punto de entrada principal
Sistema de evaluación inteligente de estados financieros con dos agentes de IA.
"""

import asyncio
import sys
import signal
from typing import Optional
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from services.telegram_service import TelegramService
from agents.secretaria_virtual import SecretariaVirtual
from agents.analista_riesgos import AnalistaRiesgos

# Configurar logging
from loguru import logger

# Configurar logger
logger.remove()  # Remover handler por defecto
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)
logger.add(
    Path(settings.LOGS_DIR) / "yateapruebo_{time:YYYY-MM-DD}.log",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="1 day",
    retention="30 days",
    compression="zip"
)

class YaTeApruebaSystem:
    """
    Sistema principal YaTeApruebo.
    
    Coordina la interacción entre los agentes de IA y los servicios
    para proporcionar evaluación inteligente de estados financieros.
    """
    
    def __init__(self):
        """Inicializa el sistema YaTeApruebo."""
        logger.info("🚀 Inicializando Sistema YaTeApruebo")
        
        # Validar configuración
        if not settings.validate_config():
            logger.error("❌ Configuración inválida. Revisa las variables de entorno.")
            sys.exit(1)
        
        # Crear directorios necesarios
        settings.create_directories()
        
        # Inicializar servicios
        self.telegram_service: Optional[TelegramService] = None
        self.secretaria: Optional[SecretariaVirtual] = None
        self.analista: Optional[AnalistaRiesgos] = None
        
        # Estado del sistema
        self.running = False
        
        logger.info("✅ Sistema YaTeApruebo inicializado correctamente")
    
    async def inicializar_servicios(self) -> None:
        """Inicializa todos los servicios del sistema."""
        try:
            logger.info("🔧 Inicializando servicios...")
            
            # Inicializar agentes
            self.secretaria = SecretariaVirtual()
            self.analista = AnalistaRiesgos()
            
            # Inicializar servicio de Telegram solo si está configurado
            if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "tu_token_aqui":
                self.telegram_service = TelegramService()
                logger.info("✅ Telegram bot configurado")
            else:
                self.telegram_service = None
                logger.warning("⚠️ Token de Telegram no configurado - solo API disponible")
            
            logger.info("✅ Todos los servicios inicializados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servicios: {str(e)}")
            raise

    async def procesar_evaluacion_directa(self, nombre_empresa: str, sector_empresa: str, archivo_pdf: str):
        """
        Procesa una evaluación directamente sin Telegram (para uso con API).
        
        Args:
            nombre_empresa: Nombre de la empresa
            sector_empresa: Sector de la empresa
            archivo_pdf: Ruta al archivo PDF
            
        Returns:
            dict: Resultado de la evaluación completa
        """
        try:
            # Generar session_id único
            import uuid
            session_id = str(uuid.uuid4())[:8]
            
            logger.info(f"🔄 Iniciando evaluación directa para {nombre_empresa} (ID: {session_id})")
            
            # Crear datos de empresa simulando input de usuario
            datos_empresa = {
                "nombre": nombre_empresa,
                "sector": sector_empresa,
                "session_id": session_id
            }
            
            # Paso 1: Procesar PDF con la secretaria
            resultado_pdf = await self.secretaria.procesar_pdf(archivo_pdf, datos_empresa)
            
            if not resultado_pdf.get("success"):
                return {"error": f"Error procesando PDF: {resultado_pdf.get('error', 'Desconocido')}"}
            
            # Paso 2: Realizar análisis con analista de riesgos
            resultado_analisis = await self.analista.realizar_analisis_completo(
                contenido_pdf=resultado_pdf["contenido_procesado"],
                datos_empresa=datos_empresa
            )
            
            if not resultado_analisis.get("success"):
                return {"error": f"Error en análisis: {resultado_analisis.get('error', 'Desconocido')}"}
            
            # Paso 3: Generar reporte
            reporte_resultado = await self.analista.generar_reporte_final(
                analisis_completo=resultado_analisis["analisis_completo"],
                datos_empresa=datos_empresa
            )
            
            if not reporte_resultado.get("success"):
                return {"error": f"Error generando reporte: {reporte_resultado.get('error', 'Desconocido')}"}
            
            # Compilar resultado final
            resultado_final = {
                "success": True,
                "session_id": session_id,
                "empresa": datos_empresa,
                "contenido_pdf": resultado_pdf["contenido_procesado"],
                "analisis_completo": resultado_analisis["analisis_completo"],
                "calificacion_riesgo": resultado_analisis["analisis_completo"]["calificacion_riesgo"],
                "reporte_completo": reporte_resultado["reporte_completo"],
                "pdf_path": reporte_resultado["pdf_path"]
            }
            
            # Guardar análisis completo para futuras consultas
            import json
            from pathlib import Path
            output_dir = Path(settings.OUTPUT_DIR)
            archivo_analisis = output_dir / f"{session_id}_analisis_completo.json"
            
            with open(archivo_analisis, 'w', encoding='utf-8') as f:
                json.dump(resultado_final, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Evaluación directa completada para {nombre_empresa}")
            return resultado_final
            
        except Exception as e:
            logger.error(f"❌ Error en evaluación directa: {e}")
            return {"error": str(e)}

    def obtener_estadisticas_sistema(self):
        """Obtiene estadísticas básicas del sistema."""
        try:
            from pathlib import Path
            import json
            
            output_dir = Path(settings.OUTPUT_DIR)
            archivos_analisis = list(output_dir.glob("*_analisis_completo.json"))
            
            total_evaluaciones = len(archivos_analisis)
            evaluaciones_por_nivel = {"BÁSICO": 0, "INTERMEDIO": 0, "AVANZADO": 0}
            
            for archivo in archivos_analisis:
                try:
                    with open(archivo, 'r', encoding='utf-8') as f:
                        analisis = json.load(f)
                    
                    nivel = analisis.get("calificacion_riesgo", {}).get("nivel")
                    if nivel in evaluaciones_por_nivel:
                        evaluaciones_por_nivel[nivel] += 1
                        
                except Exception:
                    continue
            
            return {
                "total_evaluaciones": total_evaluaciones,
                "evaluaciones_por_nivel": evaluaciones_por_nivel,
                "servicios_activos": {
                    "openai": True,  # Asumimos que está activo si el sistema se inició
                    "telegram": self.telegram_service is not None,
                    "file_service": True
                },
                "version": settings.VERSION
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    async def iniciar_sistema(self) -> None:
        """Inicia el sistema completo."""
        try:
            logger.info("🚀 Iniciando Sistema YaTeApruebo...")
            
            # Mostrar información del sistema
            self._mostrar_info_sistema()
            
            # Inicializar servicios
            await self.inicializar_servicios()
            
            # Configurar manejo de señales
            self._configurar_señales()
            
            # Iniciar bot de Telegram solo si está configurado
            if self.telegram_service:
                logger.info("📱 Iniciando bot de Telegram...")
                await self.telegram_service.iniciar_bot()
            else:
                logger.info("📱 Telegram no configurado - sistema disponible solo via API")
            
            self.running = True
            logger.info("✅ Sistema YaTeApruebo iniciado exitosamente")
            
            # Mantener el sistema ejecutándose
            await self._mantener_ejecutando()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Interrupción de teclado detectada")
            await self.detener_sistema()
        except Exception as e:
            logger.error(f"❌ Error crítico en el sistema: {str(e)}")
            await self.detener_sistema()
            sys.exit(1)
    
    async def detener_sistema(self) -> None:
        """Detiene el sistema de manera ordenada."""
        logger.info("🛑 Deteniendo Sistema YaTeApruebo...")
        
        self.running = False
        
        try:
            # Detener bot de Telegram
            if self.telegram_service:
                await self.telegram_service.detener_bot()
            
            logger.info("✅ Sistema YaTeApruebo detenido correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo sistema: {str(e)}")
    
    def _mostrar_info_sistema(self) -> None:
        """Muestra información del sistema al iniciar."""
        logger.info("=" * 60)
        logger.info(f"🏦 SISTEMA YATEAPRUEBO v{settings.VERSION}")
        logger.info(f"📄 {settings.DESCRIPTION}")
        logger.info("=" * 60)
        logger.info(f"🔧 Modo Debug: {'Activado' if settings.DEBUG else 'Desactivado'}")
        logger.info(f"📊 Modelo OpenAI: {settings.OPENAI_MODEL}")
        logger.info(f"📁 Directorio Input: {settings.INPUT_DIR}")
        logger.info(f"📁 Directorio Output: {settings.OUTPUT_DIR}")
        logger.info(f"📝 Directorio Logs: {settings.LOGS_DIR}")
        logger.info(f"🎯 Niveles de Riesgo: {', '.join(settings.RISK_LEVELS)}")
        logger.info("=" * 60)
    
    def _configurar_señales(self) -> None:
        """Configura el manejo de señales del sistema."""
        def signal_handler(signum, frame):
            logger.info(f"📡 Señal {signum} recibida. Iniciando apagado ordenado...")
            asyncio.create_task(self.detener_sistema())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _mantener_ejecutando(self) -> None:
        """Mantiene el sistema ejecutándose hasta recibir señal de parada."""
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("🔄 Tarea principal cancelada")
    
    async def procesar_evaluacion_directa(
        self, 
        nombre_empresa: str, 
        sector_empresa: str, 
        archivo_pdf: str
    ) -> dict:
        """
        Procesa una evaluación de manera directa (sin Telegram).
        Útil para integraciones API o pruebas.
        
        Args:
            nombre_empresa: Nombre de la empresa
            sector_empresa: Sector de la empresa  
            archivo_pdf: Ruta del archivo PDF
            
        Returns:
            Dict con resultado del análisis
        """
        try:
            logger.info(f"🔍 Procesando evaluación directa: {nombre_empresa}")
            
            # Asegurar que los servicios estén inicializados
            if not self.secretaria or not self.analista:
                await self.inicializar_servicios()
            
            # Simular ID de usuario para modo directo
            user_id = "direct_mode"
            
            # 1. Iniciar sesión con Secretaria Virtual
            resultado_sesion = await self.secretaria.iniciar_sesion(user_id)
            if "error" in resultado_sesion:
                return {"error": f"Error iniciando sesión: {resultado_sesion['error']}"}
            
            session_id = resultado_sesion["session_id"]
            
            # 2. Recopilar información de empresa
            resultado_info = await self.secretaria.recopilar_informacion_empresa(
                session_id, nombre_empresa, sector_empresa
            )
            if "error" in resultado_info:
                return {"error": f"Error recopilando información: {resultado_info['error']}"}
            
            # 3. Procesar archivo PDF
            resultado_pdf = await self.secretaria.procesar_archivo_pdf(session_id, archivo_pdf)
            if "error" in resultado_pdf:
                return {"error": f"Error procesando PDF: {resultado_pdf['error']}"}
            
            # 4. Preparar datos para análisis
            resultado_preparacion = await self.secretaria.preparar_datos_para_analisis(session_id)
            if "error" in resultado_preparacion:
                return {"error": f"Error preparando análisis: {resultado_preparacion['error']}"}
            
            # 5. Realizar análisis con Analista de Riesgos
            resultado_analisis = await self.analista.analizar_estado_financiero(session_id)
            if "error" in resultado_analisis:
                return {"error": f"Error en análisis: {resultado_analisis['error']}"}
            
            # 6. Generar documento final
            resultado_documento = await self.analista.generar_documento_final(session_id)
            if "error" in resultado_documento:
                return {"error": f"Error generando documento: {resultado_documento['error']}"}
            
            logger.info(f"✅ Evaluación directa completada: {nombre_empresa}")
            
            return {
                "success": True,
                "session_id": session_id,
                "empresa": nombre_empresa,
                "calificacion_riesgo": resultado_documento["reporte"]["calificacion_riesgo"],
                "pdf_path": resultado_documento["pdf_path"],
                "reporte_completo": resultado_documento["reporte"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error en evaluación directa: {str(e)}")
            return {"error": f"Error procesando evaluación: {str(e)}"}
    
    def obtener_estadisticas_sistema(self) -> dict:
        """
        Obtiene estadísticas del sistema.
        
        Returns:
            Dict con estadísticas del sistema
        """
        from services.file_service import FileService
        
        try:
            file_service = FileService()
            stats_storage = file_service.obtener_estadisticas_storage()
            
            return {
                "version": settings.VERSION,
                "estado": "ejecutando" if self.running else "detenido",
                "configuracion": {
                    "debug": settings.DEBUG,
                    "modelo_openai": settings.OPENAI_MODEL,
                    "max_tokens": settings.MAX_TOKENS,
                    "temperature": settings.TEMPERATURE
                },
                "almacenamiento": stats_storage,
                "directorios": {
                    "input": settings.INPUT_DIR,
                    "output": settings.OUTPUT_DIR,
                    "logs": settings.LOGS_DIR
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {str(e)}")
            return {"error": str(e)}

async def main():
    """Función principal del sistema."""
    sistema = YaTeApruebaSystem()
    await sistema.iniciar_sistema()

def main_sync():
    """Función principal síncrona para compatibilidad."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Sistema interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main_sync()