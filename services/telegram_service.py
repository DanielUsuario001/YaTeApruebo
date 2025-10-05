"""
Servicio de integración con Telegram Bot.
Maneja la comunicación con usuarios vía Telegram.
"""

import asyncio
from typing import Dict, Optional, List, Union
from pathlib import Path
import aiofiles

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from config.settings import settings
from agents.secretaria_virtual import SecretariaVirtual
from agents.analista_riesgos import AnalistaRiesgos
from loguru import logger

class TelegramService:
    """
    Servicio de Telegram Bot para YaTeApruebo.
    
    Funcionalidades:
    - Comunicación con usuarios
    - Recepción de archivos PDF
    - Envío de reportes
    - Gestión de sesiones de usuarios
    """
    
    def __init__(self):
        """Inicializa el servicio de Telegram."""
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.bot_token)
        self.application = Application.builder().token(self.bot_token).build()
        
        # Agentes
        self.secretaria = SecretariaVirtual()
        self.analista = AnalistaRiesgos()
        
        # Estados de usuario
        self.user_sessions = {}
        
        # Configurar handlers
        self._setup_handlers()
        
        logger.info("🤖 Servicio Telegram inicializado")
    
    def _setup_handlers(self) -> None:
        """Configura los handlers de comandos y mensajes."""
        # Comandos
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("nueva_evaluacion", self.cmd_nueva_evaluacion))
        self.application.add_handler(CommandHandler("estado", self.cmd_estado))
        self.application.add_handler(CommandHandler("cancelar", self.cmd_cancelar))
        
        # Mensajes de texto
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
        )
        
        # Documentos (PDFs)
        self.application.add_handler(
            MessageHandler(filters.Document.PDF, self.handle_pdf_document)
        )
        
        logger.debug("🔧 Handlers de Telegram configurados")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /start - Saludo inicial."""
        user_id = str(update.effective_user.id)
        username = update.effective_user.first_name or "Usuario"
        
        mensaje_bienvenida = f"""
🏦 <b>¡Bienvenido a YaTeApruebo, {username}!</b>

Soy tu asistente especializado en evaluación de estados financieros. Puedo ayudarte a:

✅ Analizar estados financieros de empresas
📊 Evaluar riesgos financieros
📋 Generar reportes profesionales
🎯 Recomendar perfiles de aprobación

<b>¿Cómo empezar?</b>
Usa el comando /nueva_evaluacion para iniciar un análisis.

<b>Comandos disponibles:</b>
/nueva_evaluacion - Iniciar nueva evaluación
/estado - Ver estado actual
/help - Mostrar ayuda
/cancelar - Cancelar proceso actual
        """
        
        await update.message.reply_text(
            mensaje_bienvenida,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"👋 Usuario {user_id} ({username}) inició bot")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /help - Ayuda del sistema."""
        mensaje_ayuda = """
🆘 <b>Ayuda de YaTeApruebo</b>

<b>¿Qué necesito para una evaluación?</b>
1. Nombre de la empresa
2. Sector de la empresa  
3. Estado financiero en formato PDF

<b>Proceso paso a paso:</b>
1️⃣ Usar /nueva_evaluacion
2️⃣ Proporcionar nombre de empresa
3️⃣ Indicar sector empresarial
4️⃣ Enviar PDF del estado financiero
5️⃣ Esperar análisis automático
6️⃣ Recibir reporte completo

<b>Tipos de archivos soportados:</b>
📄 Solo archivos PDF (máximo 10MB)
📋 Estados financieros con texto extraíble

<b>Calificaciones de riesgo:</b>
🟢 BÁSICO - Riesgo bajo
🟡 INTERMEDIO - Riesgo moderado  
🔴 AVANZADO - Riesgo alto

<b>¿Problemas?</b>
Usa /cancelar para reiniciar el proceso.
        """
        
        await update.message.reply_text(
            mensaje_ayuda,
            parse_mode=ParseMode.HTML
        )
    
    async def cmd_nueva_evaluacion(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /nueva_evaluacion - Inicia nueva evaluación."""
        user_id = str(update.effective_user.id)
        
        # Iniciar sesión con la Secretaria Virtual
        resultado = await self.secretaria.iniciar_sesion(user_id)
        
        if "error" in resultado:
            await update.message.reply_text(f"❌ Error: {resultado['error']}")
            return
        
        # Guardar sesión del usuario
        self.user_sessions[user_id] = {
            "session_id": resultado["session_id"],
            "estado": "esperando_nombre_empresa",
            "datos": {}
        }
        
        mensaje = f"""
🚀 <b>Nueva Evaluación Iniciada</b>

{resultado['mensaje']}

📝 <b>Paso 1:</b> Por favor, envíame el <b>nombre de la empresa</b> que quieres evaluar.

<i>Ejemplo: "Grupo Empresarial ABC S.A."</i>
        """
        
        await update.message.reply_text(
            mensaje,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"🆕 Nueva evaluación iniciada para usuario {user_id}")
    
    async def cmd_estado(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /estado - Muestra estado actual."""
        user_id = str(update.effective_user.id)
        
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "ℹ️ No tienes ninguna evaluación en curso.\n\nUsa /nueva_evaluacion para empezar."
            )
            return
        
        session = self.user_sessions[user_id]
        estado = session["estado"]
        
        estados_descripcion = {
            "esperando_nombre_empresa": "📝 Esperando nombre de empresa",
            "esperando_sector_empresa": "🏢 Esperando sector de empresa", 
            "esperando_archivo_pdf": "📄 Esperando archivo PDF",
            "procesando_archivo": "⚙️ Procesando archivo...",
            "preparando_analisis": "📊 Preparando análisis...",
            "analizando": "🔍 Realizando análisis financiero...",
            "generando_reporte": "📋 Generando reporte...",
            "completado": "✅ Evaluación completada"
        }
        
        descripcion = estados_descripcion.get(estado, estado)
        
        mensaje = f"""
📊 <b>Estado de tu Evaluación</b>

<b>Estado actual:</b> {descripcion}

<b>Datos recopilados:</b>
"""
        
        datos = session.get("datos", {})
        if "empresa" in datos:
            mensaje += f"• Empresa: {datos['empresa']}\n"
        if "sector" in datos:
            mensaje += f"• Sector: {datos['sector']}\n"
        if "archivo" in datos:
            mensaje += f"• Archivo: ✅ Recibido\n"
        
        await update.message.reply_text(
            mensaje,
            parse_mode=ParseMode.HTML
        )
    
    async def cmd_cancelar(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /cancelar - Cancela proceso actual."""
        user_id = str(update.effective_user.id)
        
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            mensaje = "❌ Evaluación cancelada.\n\nUsa /nueva_evaluacion cuando quieras empezar de nuevo."
        else:
            mensaje = "ℹ️ No hay ninguna evaluación en curso para cancelar."
        
        await update.message.reply_text(mensaje)
        
        logger.info(f"❌ Usuario {user_id} canceló evaluación")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja mensajes de texto según el estado del usuario."""
        user_id = str(update.effective_user.id)
        texto = update.message.text.strip()
        
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "ℹ️ Para empezar una evaluación, usa el comando /nueva_evaluacion"
            )
            return
        
        session = self.user_sessions[user_id]
        estado = session["estado"]
        session_id = session["session_id"]
        
        try:
            if estado == "esperando_nombre_empresa":
                await self._procesar_nombre_empresa(update, user_id, session_id, texto)
                
            elif estado == "esperando_sector_empresa":
                await self._procesar_sector_empresa(update, user_id, session_id, texto)
                
            else:
                await update.message.reply_text(
                    f"ℹ️ En este momento necesito que {estado.replace('esperando_', '')}."
                )
                
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje de texto: {str(e)}")
            await update.message.reply_text(
                "❌ Ocurrió un error procesando tu mensaje. Intenta de nuevo."
            )
    
    async def _procesar_nombre_empresa(
        self, 
        update: Update, 
        user_id: str, 
        session_id: str, 
        nombre_empresa: str
    ) -> None:
        """Procesa el nombre de empresa."""
        if len(nombre_empresa) < 3:
            await update.message.reply_text(
                "❌ El nombre de la empresa debe tener al menos 3 caracteres."
            )
            return
        
        # Guardar nombre
        self.user_sessions[user_id]["datos"]["empresa"] = nombre_empresa
        self.user_sessions[user_id]["estado"] = "esperando_sector_empresa"
        
        mensaje = f"""
✅ <b>Empresa registrada:</b> {nombre_empresa}

📝 <b>Paso 2:</b> Ahora envíame el <b>sector de la empresa</b>.

<i>Ejemplos: "Manufacturero", "Servicios", "Comercio", "Tecnología", "Construcción", etc.</i>
        """
        
        await update.message.reply_text(
            mensaje,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"✅ Nombre empresa guardado: {nombre_empresa}")
    
    async def _procesar_sector_empresa(
        self, 
        update: Update, 
        user_id: str, 
        session_id: str, 
        sector_empresa: str
    ) -> None:
        """Procesa el sector de empresa."""
        if len(sector_empresa) < 3:
            await update.message.reply_text(
                "❌ El sector debe tener al menos 3 caracteres."
            )
            return
        
        # Procesar con la Secretaria Virtual
        nombre_empresa = self.user_sessions[user_id]["datos"]["empresa"]
        
        resultado = await self.secretaria.recopilar_informacion_empresa(
            session_id, nombre_empresa, sector_empresa
        )
        
        if "error" in resultado:
            await update.message.reply_text(f"❌ Error: {resultado['error']}")
            return
        
        # Actualizar estado
        self.user_sessions[user_id]["datos"]["sector"] = sector_empresa
        self.user_sessions[user_id]["estado"] = "esperando_archivo_pdf"
        
        mensaje = f"""
✅ <b>Información empresarial completa:</b>
• Empresa: {nombre_empresa}
• Sector: {sector_empresa}

📄 <b>Paso 3:</b> Envíame el <b>estado financiero en PDF</b>.

<b>Requisitos del archivo:</b>
• Formato: PDF únicamente
• Tamaño máximo: 10MB
• Debe contener texto extraíble (no escaneado)

📎 Simplemente arrastra el archivo o usa el clip para adjuntarlo.
        """
        
        await update.message.reply_text(
            mensaje,
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"✅ Sector empresa guardado: {sector_empresa}")
    
    async def handle_pdf_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja archivos PDF recibidos."""
        user_id = str(update.effective_user.id)
        
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "ℹ️ Para enviar un archivo, primero inicia una evaluación con /nueva_evaluacion"
            )
            return
        
        session = self.user_sessions[user_id]
        
        if session["estado"] != "esperando_archivo_pdf":
            await update.message.reply_text(
                "ℹ️ En este momento no estoy esperando un archivo. Completa los pasos anteriores primero."
            )
            return
        
        try:
            # Actualizar estado
            self.user_sessions[user_id]["estado"] = "procesando_archivo"
            
            await update.message.reply_text(
                "📄 Archivo recibido. Procesando...\n\n⏳ Esto puede tomar unos momentos."
            )
            
            # Descargar archivo
            file = await context.bot.get_file(update.message.document.file_id)
            archivo_temp = f"/tmp/{user_id}_{update.message.document.file_name}"
            await file.download_to_drive(archivo_temp)
            
            # Procesar con la Secretaria Virtual
            session_id = session["session_id"]
            
            resultado_archivo = await self.secretaria.procesar_archivo_pdf(session_id, archivo_temp)
            
            if "error" in resultado_archivo:
                await update.message.reply_text(f"❌ Error procesando archivo: {resultado_archivo['error']}")
                self.user_sessions[user_id]["estado"] = "esperando_archivo_pdf"
                return
            
            # Preparar datos para análisis
            self.user_sessions[user_id]["estado"] = "preparando_analisis"
            
            await update.message.reply_text(
                "✅ Archivo procesado correctamente.\n\n📊 Preparando análisis..."
            )
            
            resultado_preparacion = await self.secretaria.preparar_datos_para_analisis(session_id)
            
            if "error" in resultado_preparacion:
                await update.message.reply_text(f"❌ Error preparando análisis: {resultado_preparacion['error']}")
                return
            
            # Iniciar análisis con el Analista de Riesgos
            await self._realizar_analisis_completo(update, user_id, session_id)
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF: {str(e)}")
            await update.message.reply_text(
                "❌ Error procesando el archivo. Verifica que sea un PDF válido e intenta de nuevo."
            )
            self.user_sessions[user_id]["estado"] = "esperando_archivo_pdf"
    
    async def _realizar_analisis_completo(
        self, 
        update: Update, 
        user_id: str, 
        session_id: str
    ) -> None:
        """Realiza el análisis completo con el Analista de Riesgos."""
        try:
            # Actualizar estado
            self.user_sessions[user_id]["estado"] = "analizando"
            
            await update.message.reply_text(
                "🔍 <b>Iniciando análisis financiero...</b>\n\n⏳ Nuestro Analista Senior está evaluando el estado financiero. Esto puede tomar algunos minutos.",
                parse_mode=ParseMode.HTML
            )
            
            # Realizar análisis
            resultado_analisis = await self.analista.analizar_estado_financiero(session_id)
            
            if "error" in resultado_analisis:
                await update.message.reply_text(f"❌ Error en análisis: {resultado_analisis['error']}")
                return
            
            # Generar documento final
            self.user_sessions[user_id]["estado"] = "generando_reporte"
            
            await update.message.reply_text(
                "📋 Análisis completado. Generando reporte final..."
            )
            
            resultado_documento = await self.analista.generar_documento_final(session_id)
            
            if "error" in resultado_documento:
                await update.message.reply_text(f"❌ Error generando documento: {resultado_documento['error']}")
                return
            
            # Enviar reporte
            await self._enviar_reporte_final(update, user_id, resultado_documento)
            
        except Exception as e:
            logger.error(f"❌ Error en análisis completo: {str(e)}")
            await update.message.reply_text(
                "❌ Error durante el análisis. Por favor intenta de nuevo más tarde."
            )
    
    async def _enviar_reporte_final(
        self, 
        update: Update, 
        user_id: str, 
        resultado_documento: Dict
    ) -> None:
        """Envía el reporte final al usuario."""
        try:
            reporte = resultado_documento["reporte"]
            pdf_path = resultado_documento["pdf_path"]
            
            # Mensaje con resumen
            calificacion = reporte["calificacion_riesgo"]
            empresa = reporte["empresa"]["nombre"]
            
            # Determinar emoji según calificación
            emoji_riesgo = {
                "BASICO": "🟢",
                "INTERMEDIO": "🟡", 
                "AVANZADO": "🔴"
            }.get(calificacion["nivel"], "🟡")
            
            mensaje_resumen = f"""
🎉 <b>¡Análisis Completado!</b>

🏢 <b>Empresa:</b> {empresa}
{emoji_riesgo} <b>Calificación de Riesgo:</b> {calificacion["nivel"]}
📊 <b>Puntuación:</b> {calificacion.get("puntuacion", "N/A")}/100

<b>📋 Resumen Ejecutivo:</b>
{reporte.get("resumen_ejecutivo", "No disponible")[:500]}...

<b>👤 Perfil Recomendado para Aprobación:</b>
{reporte["perfil_aprobador"]["perfil"]}

📄 El reporte completo se enviará como archivo PDF.
            """
            
            await update.message.reply_text(
                mensaje_resumen,
                parse_mode=ParseMode.HTML
            )
            
            # Enviar archivo PDF
            if Path(pdf_path).exists():
                with open(pdf_path, 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=pdf_file,
                        filename=f"Reporte_Financiero_{empresa.replace(' ', '_')}.pdf",
                        caption="📊 <b>Reporte Financiero Completo</b>\n\n✅ Análisis realizado por YaTeApruebo",
                        parse_mode=ParseMode.HTML
                    )
            
            # Actualizar estado final
            self.user_sessions[user_id]["estado"] = "completado"
            
            await update.message.reply_text(
                "✅ <b>Evaluación finalizada exitosamente.</b>\n\nUsa /nueva_evaluacion para analizar otra empresa.",
                parse_mode=ParseMode.HTML
            )
            
            logger.info(f"✅ Reporte enviado exitosamente a usuario {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando reporte: {str(e)}")
            await update.message.reply_text(
                "❌ Error enviando el reporte. El análisis se completó pero hubo un problema con la entrega."
            )
    
    async def iniciar_bot(self) -> None:
        """Inicia el bot de Telegram."""
        try:
            logger.info("🚀 Iniciando bot de Telegram...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("✅ Bot de Telegram iniciado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando bot: {str(e)}")
            raise
    
    async def detener_bot(self) -> None:
        """Detiene el bot de Telegram."""
        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            logger.info("🛑 Bot de Telegram detenido")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo bot: {str(e)}")
    
    async def enviar_mensaje_directo(self, user_id: str, mensaje: str) -> Dict:
        """
        Envía un mensaje directo a un usuario específico.
        
        Args:
            user_id: ID del usuario
            mensaje: Mensaje a enviar
            
        Returns:
            Dict con resultado del envío
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=mensaje,
                parse_mode=ParseMode.HTML
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje directo: {str(e)}")
            return {"success": False, "error": str(e)}