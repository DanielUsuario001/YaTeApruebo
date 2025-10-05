"""
Servicio de integración con OpenAI API.
Maneja las comunicaciones con los modelos de IA.
"""

import asyncio
from typing import Dict, Optional, List
import openai
from openai import AsyncOpenAI

from config.settings import settings
from loguru import logger

class OpenAIService:
    """
    Servicio para interactuar con la API de OpenAI.
    
    Proporciona métodos para generar respuestas usando diferentes modelos
    y configuraciones según el agente que lo utilice.
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa el servicio de OpenAI.
        
        Args:
            api_key: Clave API de OpenAI
        """
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        
        logger.info("🤖 Servicio OpenAI inicializado")
    
    async def generar_respuesta(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Genera una respuesta usando OpenAI.
        
        Args:
            prompt: Mensaje principal para el modelo
            system_message: Mensaje de sistema (opcional)
            model: Modelo específico a usar (opcional)
            max_tokens: Número máximo de tokens (opcional)
            temperature: Temperatura para la generación (opcional)
            
        Returns:
            Respuesta generada por el modelo
            
        Raises:
            Exception: Si hay error en la comunicación con OpenAI
        """
        try:
            # Usar parámetros por defecto si no se especifican
            model_to_use = model or self.model
            max_tokens_to_use = max_tokens or self.max_tokens
            temperature_to_use = temperature or self.temperature
            
            # Preparar mensajes
            messages = []
            
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            logger.debug(f"📤 Enviando petición a OpenAI - Modelo: {model_to_use}")
            
            # Realizar petición a OpenAI
            response = await self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=max_tokens_to_use,
                temperature=temperature_to_use,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extraer respuesta
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                logger.debug(f"📥 Respuesta recibida de OpenAI ({len(content)} caracteres)")
                
                return content.strip()
            else:
                raise Exception("No se recibió respuesta válida de OpenAI")
                
        except openai.RateLimitError as e:
            logger.error(f"❌ Límite de rate alcanzado en OpenAI: {str(e)}")
            raise Exception("Límite de uso de API alcanzado. Intenta más tarde.")
            
        except openai.AuthenticationError as e:
            logger.error(f"❌ Error de autenticación en OpenAI: {str(e)}")
            raise Exception("Error de autenticación con OpenAI API")
            
        except openai.APIError as e:
            logger.error(f"❌ Error de API de OpenAI: {str(e)}")
            raise Exception(f"Error en API de OpenAI: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ Error inesperado en OpenAI: {str(e)}")
            raise Exception(f"Error en comunicación con OpenAI: {str(e)}")
    
    async def generar_respuesta_streaming(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        callback = None
    ) -> str:
        """
        Genera una respuesta en modo streaming (para respuestas largas).
        
        Args:
            prompt: Mensaje principal
            system_message: Mensaje de sistema (opcional)
            callback: Función callback para procesar chunks (opcional)
            
        Returns:
            Respuesta completa generada
        """
        try:
            messages = []
            
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            logger.debug("📤 Iniciando streaming de OpenAI")
            
            full_response = ""
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    
                    # Llamar callback si está disponible
                    if callback:
                        await callback(content_chunk)
            
            logger.debug(f"📥 Streaming completado ({len(full_response)} caracteres)")
            
            return full_response.strip()
            
        except Exception as e:
            logger.error(f"❌ Error en streaming de OpenAI: {str(e)}")
            raise Exception(f"Error en streaming: {str(e)}")
    
    async def analizar_documento_con_contexto(
        self, 
        contenido_documento: str,
        contexto_empresa: Dict,
        tipo_analisis: str
    ) -> str:
        """
        Realiza análisis especializado de documentos con contexto empresarial.
        
        Args:
            contenido_documento: Contenido del documento a analizar
            contexto_empresa: Información contextual de la empresa
            tipo_analisis: Tipo de análisis a realizar
            
        Returns:
            Análisis especializado del documento
        """
        system_message = f"""
        Eres un analista financiero senior especializado en {tipo_analisis}.
        
        Información del contexto:
        - Empresa: {contexto_empresa.get('nombre', 'N/A')}
        - Sector: {contexto_empresa.get('sector', 'N/A')}
        - Fecha: {contexto_empresa.get('fecha', 'N/A')}
        
        Tu análisis debe ser:
        1. Técnicamente riguroso
        2. Específico para el sector
        3. Orientado a la evaluación de riesgos
        4. Basado en mejores prácticas financieras
        5. Claro y accionable
        
        Proporciona siempre conclusiones numéricas cuando sea posible.
        """
        
        prompt = f"""
        Analiza el siguiente documento financiero para {tipo_analisis}:
        
        DOCUMENTO:
        {contenido_documento}
        
        Proporciona un análisis detallado que incluya:
        1. Indicadores clave calculados
        2. Interpretación de los resultados
        3. Comparación con estándares del sector
        4. Identificación de riesgos y oportunidades
        5. Recomendaciones específicas
        
        Estructura tu respuesta de manera profesional y utiliza formato JSON para datos numéricos.
        """
        
        return await self.generar_respuesta(
            prompt=prompt,
            system_message=system_message,
            temperature=0.1  # Menos creatividad para análisis financieros
        )
    
    async def validar_conexion(self) -> Dict:
        """
        Valida que la conexión con OpenAI esté funcionando.
        
        Returns:
            Dict con resultado de la validación
        """
        try:
            # Hacer una petición simple de prueba
            test_response = await self.generar_respuesta(
                prompt="Responde solo con 'OK' si recibes este mensaje.",
                max_tokens=10
            )
            
            if "OK" in test_response:
                logger.info("✅ Conexión con OpenAI validada correctamente")
                return {
                    "valid": True,
                    "message": "Conexión exitosa",
                    "model": self.model
                }
            else:
                return {
                    "valid": False,
                    "message": "Respuesta inesperada en validación"
                }
                
        except Exception as e:
            logger.error(f"❌ Error validando conexión OpenAI: {str(e)}")
            return {
                "valid": False,
                "message": f"Error de conexión: {str(e)}"
            }
    
    def cambiar_configuracion(
        self, 
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> None:
        """
        Cambia la configuración del servicio OpenAI.
        
        Args:
            model: Nuevo modelo a usar
            max_tokens: Nuevos tokens máximos
            temperature: Nueva temperatura
        """
        if model:
            self.model = model
            logger.info(f"🔄 Modelo cambiado a: {model}")
        
        if max_tokens:
            self.max_tokens = max_tokens
            logger.info(f"🔄 Max tokens cambiado a: {max_tokens}")
        
        if temperature is not None:
            self.temperature = temperature
            logger.info(f"🔄 Temperature cambiada a: {temperature}")
    
    def obtener_estadisticas_uso(self) -> Dict:
        """
        Obtiene estadísticas básicas de uso del servicio.
        
        Returns:
            Dict con estadísticas de uso
        """
        return {
            "model_actual": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_key_configurada": bool(self.api_key)
        }