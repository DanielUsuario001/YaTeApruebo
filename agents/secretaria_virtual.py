"""
Agente 1: Secretaria Virtual
Responsable de la recopilación de información inicial y gestión de documentos.
"""

import asyncio
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import json

from services.openai_service import OpenAIService
from services.file_service import FileService
from utils.validators import DataValidator
from config.settings import settings
from loguru import logger

class SecretariaVirtual:
    """
    Agente 1: Secretaria Virtual
    
    Funciones principales:
    - Recopilar información de la empresa
    - Validar y almacenar archivos PDF
    - Preparar datos para el análisis
    - Gestionar la comunicación inicial con el usuario
    """
    
    def __init__(self):
        """Inicializa la Secretaria Virtual."""
        self.openai_service = OpenAIService(api_key=settings.OPENAI_API_KEY_AGENTE1)
        self.file_service = FileService()
        self.validator = DataValidator()
        self.session_data = {}
        
        logger.info("🤖 Secretaria Virtual inicializada")
    
    async def iniciar_sesion(self, user_id: str) -> Dict:
        """
        Inicia una nueva sesión de evaluación.
        
        Args:
            user_id: ID único del usuario
            
        Returns:
            Dict con información de la sesión
        """
        session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session_data[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "status": "iniciada",
            "empresa": {},
            "archivos": [],
            "progreso": "recopilacion_datos"
        }
        
        logger.info(f"📋 Nueva sesión iniciada: {session_id}")
        
        return {
            "session_id": session_id,
            "mensaje": "¡Hola! Soy tu Secretaria Virtual de YaTeApruebo. Te ayudaré a analizar el estado financiero de tu empresa.",
            "siguiente_paso": "solicitar_nombre_empresa"
        }
    
    async def recopilar_informacion_empresa(self, session_id: str, nombre_empresa: str, sector_empresa: str) -> Dict:
        """
        Recopila y valida la información básica de la empresa.
        
        Args:
            session_id: ID de la sesión
            nombre_empresa: Nombre de la empresa
            sector_empresa: Sector de la empresa
            
        Returns:
            Dict con resultado de la validación
        """
        if session_id not in self.session_data:
            return {"error": "Sesión no encontrada"}
        
        # Validar datos de entrada
        if not self.validator.validar_nombre_empresa(nombre_empresa):
            return {"error": "Nombre de empresa inválido"}
        
        if not self.validator.validar_sector_empresa(sector_empresa):
            return {"error": "Sector de empresa inválido"}
        
        # Guardar información
        self.session_data[session_id]["empresa"] = {
            "nombre": nombre_empresa.strip(),
            "sector": sector_empresa.strip(),
            "fecha_registro": datetime.now().isoformat()
        }
        
        self.session_data[session_id]["progreso"] = "informacion_recopilada"
        
        logger.info(f"🏢 Información de empresa registrada: {nombre_empresa} - {sector_empresa}")
        
        return {
            "success": True,
            "mensaje": f"Perfecto! He registrado los datos de {nombre_empresa} del sector {sector_empresa}.",
            "siguiente_paso": "solicitar_archivo_pdf"
        }
    
    async def procesar_archivo_pdf(self, session_id: str, archivo_path: str) -> Dict:
        """
        Procesa y valida el archivo PDF del estado financiero.
        
        Args:
            session_id: ID de la sesión
            archivo_path: Ruta del archivo PDF
            
        Returns:
            Dict con resultado del procesamiento
        """
        if session_id not in self.session_data:
            return {"error": "Sesión no encontrada"}
        
        try:
            # Validar archivo
            validacion = await self.file_service.validar_archivo_pdf(archivo_path)
            if not validacion["valido"]:
                return {"error": f"Archivo inválido: {validacion['razon']}"}
            
            # Guardar archivo
            archivo_guardado = await self.file_service.guardar_archivo_input(
                archivo_path, 
                session_id,
                self.session_data[session_id]["empresa"]["nombre"]
            )
            
            # Actualizar sesión
            self.session_data[session_id]["archivos"].append({
                "path_original": archivo_path,
                "path_guardado": archivo_guardado["path"],
                "nombre_archivo": archivo_guardado["nombre"],
                "tamaño": archivo_guardado["tamaño"],
                "fecha_subida": datetime.now().isoformat()
            })
            
            self.session_data[session_id]["progreso"] = "archivo_procesado"
            
            logger.info(f"📄 Archivo PDF procesado correctamente: {archivo_guardado['nombre']}")
            
            return {
                "success": True,
                "mensaje": "¡Excelente! He recibido y validado el estado financiero.",
                "archivo_info": archivo_guardado,
                "siguiente_paso": "preparar_analisis"
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando archivo PDF: {str(e)}")
            return {"error": f"Error procesando archivo: {str(e)}"}
    
    async def preparar_datos_para_analisis(self, session_id: str) -> Dict:
        """
        Prepara los datos recopilados para el análisis del Agente 2.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Dict con datos preparados para análisis
        """
        if session_id not in self.session_data:
            return {"error": "Sesión no encontrada"}
        
        sesion = self.session_data[session_id]
        
        if sesion["progreso"] != "archivo_procesado":
            return {"error": "Proceso incompleto. Falta información o archivo."}
        
        try:
            # Extraer texto del PDF
            archivo_info = sesion["archivos"][0]
            contenido_pdf = await self.file_service.extraer_texto_pdf(archivo_info["path_guardado"])
            
            # Preparar prompt especializado para el análisis
            prompt_contexto = await self._generar_prompt_contexto(sesion["empresa"], contenido_pdf)
            
            # Guardar datos preparados
            datos_analisis = {
                "session_id": session_id,
                "empresa": sesion["empresa"],
                "archivo_financiero": archivo_info,
                "contenido_extraido": contenido_pdf,
                "prompt_contexto": prompt_contexto,
                "fecha_preparacion": datetime.now().isoformat(),
                "estado": "listo_para_analisis"
            }
            
            # Guardar en archivo JSON para el Agente 2
            archivo_datos = Path(settings.INPUT_DIR) / f"{session_id}_datos_analisis.json"
            with open(archivo_datos, 'w', encoding='utf-8') as f:
                json.dump(datos_analisis, f, ensure_ascii=False, indent=2)
            
            sesion["progreso"] = "datos_preparados"
            sesion["archivo_datos_analisis"] = str(archivo_datos)
            
            logger.info(f"📊 Datos preparados para análisis: {session_id}")
            
            return {
                "success": True,
                "mensaje": "¡Perfecto! He preparado todos los datos. Ahora nuestro Analista Senior se encargará del análisis financiero.",
                "datos_analisis": datos_analisis,
                "siguiente_paso": "enviar_a_analista"
            }
            
        except Exception as e:
            logger.error(f"❌ Error preparando datos para análisis: {str(e)}")
            return {"error": f"Error preparando datos: {str(e)}"}
    
    async def _generar_prompt_contexto(self, empresa_info: Dict, contenido_pdf: str) -> str:
        """
        Genera un prompt contextualizado para el análisis financiero.
        
        Args:
            empresa_info: Información de la empresa
            contenido_pdf: Contenido extraído del PDF
            
        Returns:
            Prompt especializado para el análisis
        """
        prompt = f"""
        ANÁLISIS FINANCIERO REQUERIDO
        
        INFORMACIÓN DE LA EMPRESA:
        - Nombre: {empresa_info['nombre']}
        - Sector: {empresa_info['sector']}
        - Fecha de análisis: {datetime.now().strftime('%d/%m/%Y')}
        
        CONTEXTO DEL SECTOR:
        Empresa del sector {empresa_info['sector']}. Considerar las particularidades y riesgos típicos de este sector.
        
        DOCUMENTO FINANCIERO:
        El estado financiero contiene la siguiente información:
        {contenido_pdf[:2000]}...
        
        OBJETIVO DEL ANÁLISIS:
        Realizar un análisis exhaustivo como analista senior de riesgos financieros, evaluando:
        1. Liquidez y solvencia
        2. Rentabilidad
        3. Endeudamiento
        4. Eficiencia operativa
        5. Riesgos específicos del sector
        
        Proporcionar una calificación de riesgo: BÁSICO, INTERMEDIO o AVANZADO.
        """
        
        return prompt
    
    def obtener_resumen_sesion(self, session_id: str) -> Dict:
        """
        Obtiene un resumen de la sesión actual.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Dict con resumen de la sesión
        """
        if session_id not in self.session_data:
            return {"error": "Sesión no encontrada"}
        
        sesion = self.session_data[session_id]
        
        return {
            "session_id": session_id,
            "progreso": sesion["progreso"],
            "empresa": sesion.get("empresa", {}),
            "archivos_count": len(sesion.get("archivos", [])),
            "estado": "En proceso" if sesion["progreso"] != "completado" else "Completado",
            "created_at": sesion["created_at"]
        }