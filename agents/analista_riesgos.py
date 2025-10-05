"""
Agente 2: Analista de Riesgos Senior
Especialista en análisis financiero exhaustivo y evaluación de riesgos.
"""

import asyncio
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from services.openai_service import OpenAIService
from utils.report_generator import ReportGenerator
from config.settings import settings
from loguru import logger

class AnalistaRiesgos:
    """
    Agente 2: Analista de Riesgos Senior
    
    Funciones principales:
    - Análisis exhaustivo de estados financieros
    - Evaluación de riesgos financieros
    - Generación de calificaciones de riesgo
    - Recomendaciones de perfiles de aprobación
    """
    
    def __init__(self):
        """Inicializa el Analista de Riesgos."""
        self.openai_service = OpenAIService(api_key=settings.OPENAI_SEGUNDO_AGENTE)
        self.report_generator = ReportGenerator()
        
        # Criterios de análisis
        self.criterios_analisis = {
            "liquidez": ["ratio_corriente", "prueba_acida", "capital_trabajo"],
            "solvencia": ["ratio_deuda_patrimonio", "cobertura_intereses", "apalancamiento"],
            "rentabilidad": ["roe", "roa", "margen_neto", "margen_operacional"],
            "eficiencia": ["rotacion_activos", "rotacion_inventarios", "periodo_cobro"],
            "crecimiento": ["ventas", "utilidades", "activos"]
        }
        
        logger.info("🎯 Analista de Riesgos Senior inicializado")
    
    async def analizar_estado_financiero(self, session_id: str) -> Dict:
        """
        Realiza el análisis completo del estado financiero.
        
        Args:
            session_id: ID de la sesión a analizar
            
        Returns:
            Dict con resultado del análisis completo
        """
        try:
            # Cargar datos preparados por la Secretaria Virtual
            datos_analisis = await self._cargar_datos_analisis(session_id)
            if "error" in datos_analisis:
                return datos_analisis
            
            logger.info(f"📊 Iniciando análisis financiero para: {datos_analisis['empresa']['nombre']}")
            
            # Realizar análisis por categorías
            analisis_resultados = {}
            
            # 1. Análisis de liquidez
            analisis_resultados["liquidez"] = await self._analizar_liquidez(datos_analisis)
            
            # 2. Análisis de solvencia
            analisis_resultados["solvencia"] = await self._analizar_solvencia(datos_analisis)
            
            # 3. Análisis de rentabilidad
            analisis_resultados["rentabilidad"] = await self._analizar_rentabilidad(datos_analisis)
            
            # 4. Análisis de eficiencia
            analisis_resultados["eficiencia"] = await self._analizar_eficiencia(datos_analisis)
            
            # 5. Análisis sectorial
            analisis_resultados["sectorial"] = await self._analizar_riesgo_sectorial(datos_analisis)
            
            # Generar calificación global
            calificacion_riesgo = await self._generar_calificacion_riesgo(analisis_resultados)
            
            # Preparar reporte final
            reporte_final = {
                "session_id": session_id,
                "empresa": datos_analisis["empresa"],
                "fecha_analisis": datetime.now().isoformat(),
                "analisis_detallado": analisis_resultados,
                "calificacion_riesgo": calificacion_riesgo,
                "recomendaciones": await self._generar_recomendaciones(calificacion_riesgo, analisis_resultados),
                "perfil_aprobador": self._determinar_perfil_aprobador(calificacion_riesgo),
                "resumen_ejecutivo": await self._generar_resumen_ejecutivo(analisis_resultados, calificacion_riesgo)
            }
            
            # Guardar análisis completo
            await self._guardar_analisis(session_id, reporte_final)
            
            logger.info(f"✅ Análisis completado. Calificación: {calificacion_riesgo['nivel']}")
            
            return {
                "success": True,
                "reporte_final": reporte_final,
                "siguiente_paso": "generar_documento"
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis financiero: {str(e)}")
            return {"error": f"Error en análisis: {str(e)}"}
    
    async def _cargar_datos_analisis(self, session_id: str) -> Dict:
        """Carga los datos preparados por la Secretaria Virtual."""
        archivo_datos = Path(settings.INPUT_DIR) / f"{session_id}_datos_analisis.json"
        
        if not archivo_datos.exists():
            return {"error": "Datos de análisis no encontrados"}
        
        try:
            with open(archivo_datos, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            return datos
        except Exception as e:
            return {"error": f"Error cargando datos: {str(e)}"}
    
    async def _analizar_liquidez(self, datos: Dict) -> Dict:
        """Analiza los indicadores de liquidez."""
        prompt = f"""
        Como analista senior de riesgos, analiza la liquidez de la empresa {datos['empresa']['nombre']} 
        del sector {datos['empresa']['sector']}.
        
        Basándote en el siguiente estado financiero:
        {datos['contenido_extraido'][:1500]}
        
        Evalúa:
        1. Ratio corriente (activo corriente / pasivo corriente)
        2. Prueba ácida ((activo corriente - inventarios) / pasivo corriente)
        3. Capital de trabajo (activo corriente - pasivo corriente)
        4. Disponibilidad inmediata
        
        Proporciona:
        - Valores calculados
        - Interpretación de cada ratio
        - Riesgo de liquidez (BAJO, MEDIO, ALTO)
        - Observaciones específicas
        
        Responde en formato JSON con esta estructura:
        {{
            "ratios": {{}},
            "interpretacion": "",
            "riesgo_liquidez": "BAJO|MEDIO|ALTO",
            "observaciones": []
        }}
        """
        
        try:
            logger.info("🔄 Solicitando análisis de liquidez a OpenAI...")
            response = await self.openai_service.generar_respuesta_json(prompt)
            
            logger.debug(f"📥 Respuesta de OpenAI recibida: {response[:200]}...")
            
            # Verificar que la respuesta no esté vacía
            if not response or response.strip() == "":
                logger.error("❌ Respuesta vacía de OpenAI")
                return {
                    "categoria": "liquidez",
                    "resultado": {
                        "ratios": {},
                        "interpretacion": "No se pudo realizar el análisis por falta de respuesta del modelo",
                        "riesgo_liquidez": "MEDIO",
                        "observaciones": ["Error en análisis automático"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            analisis = json.loads(response)
            
            # Verificar si hay error en la respuesta
            if "error" in analisis:
                logger.error(f"Error en respuesta de análisis de liquidez: {analisis['error']}")
                return {
                    "categoria": "liquidez",
                    "resultado": {
                        "ratios": {},
                        "interpretacion": f"Error en análisis: {analisis.get('error', 'Desconocido')}",
                        "riesgo_liquidez": "MEDIO",
                        "observaciones": ["Error en procesamiento"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.success("✅ Análisis de liquidez completado")
            return {
                "categoria": "liquidez",
                "resultado": analisis,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON en análisis de liquidez: {str(e)}")
            logger.debug(f"Respuesta que causó error: {response if 'response' in locals() else 'N/A'}")
            return {
                "categoria": "liquidez",
                "resultado": {
                    "ratios": {},
                    "interpretacion": "Error en formato de respuesta del modelo de IA",
                    "riesgo_liquidez": "MEDIO",
                    "observaciones": ["Respuesta inválida del modelo"]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en análisis de liquidez: {str(e)}")
            return {
                "categoria": "liquidez",
                "resultado": {
                    "ratios": {},
                    "interpretacion": f"Error inesperado: {str(e)}",
                    "riesgo_liquidez": "MEDIO",
                    "observaciones": ["Error en procesamiento"]
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analizar_solvencia(self, datos: Dict) -> Dict:
        """Analiza los indicadores de solvencia."""
        prompt = f"""
        Como analista senior, evalúa la solvencia de {datos['empresa']['nombre']} 
        del sector {datos['empresa']['sector']}.
        
        Estado financiero:
        {datos['contenido_extraido'][:1500]}
        
        Analiza:
        1. Ratio de endeudamiento (pasivo total / activo total)
        2. Ratio deuda/patrimonio
        3. Cobertura de intereses
        4. Apalancamiento financiero
        5. Capacidad de pago a largo plazo
        
        Evalúa el riesgo de insolvencia y proporciona análisis detallado.
        
        Responde en formato JSON con esta estructura:
        {{
            "ratios": {{}},
            "evaluacion": "",
            "riesgo_insolvencia": "BAJO|MEDIO|ALTO",
            "recomendaciones": []
        }}
        """
        
        try:
            logger.info("🔄 Solicitando análisis de solvencia a OpenAI...")
            response = await self.openai_service.generar_respuesta_json(prompt)
            
            logger.debug(f"📥 Respuesta de OpenAI recibida: {response[:200]}...")
            
            # Verificar que la respuesta no esté vacía
            if not response or response.strip() == "":
                logger.error("❌ Respuesta vacía de OpenAI")
                return {
                    "categoria": "solvencia",
                    "resultado": {
                        "ratios": {},
                        "evaluacion": "No se pudo realizar el análisis por falta de respuesta del modelo",
                        "riesgo_insolvencia": "MEDIO",
                        "recomendaciones": ["Error en análisis automático"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            analisis = json.loads(response)
            
            # Verificar si hay error en la respuesta
            if "error" in analisis:
                logger.error(f"Error en respuesta de análisis de solvencia: {analisis['error']}")
                return {
                    "categoria": "solvencia",
                    "resultado": {
                        "ratios": {},
                        "evaluacion": f"Error en análisis: {analisis.get('error', 'Desconocido')}",
                        "riesgo_insolvencia": "MEDIO",
                        "recomendaciones": ["Error en procesamiento"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.success("✅ Análisis de solvencia completado")
            return {
                "categoria": "solvencia",
                "resultado": analisis,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON en análisis de solvencia: {str(e)}")
            logger.debug(f"Respuesta que causó error: {response if 'response' in locals() else 'N/A'}")
            return {
                "categoria": "solvencia",
                "resultado": {
                    "ratios": {},
                    "evaluacion": "Error en formato de respuesta del modelo de IA",
                    "riesgo_insolvencia": "MEDIO",
                    "recomendaciones": ["Respuesta inválida del modelo"]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en análisis de solvencia: {str(e)}")
            return {
                "categoria": "solvencia",
                "resultado": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analizar_rentabilidad(self, datos: Dict) -> Dict:
        """Analiza los indicadores de rentabilidad."""
        prompt = f"""
        Evalúa la rentabilidad de {datos['empresa']['nombre']} como analista experto.
        
        Sector: {datos['empresa']['sector']}
        Estado financiero:
        {datos['contenido_extraido'][:1500]}
        
        Calcula y analiza:
        1. ROE (Return on Equity)
        2. ROA (Return on Assets)
        3. Margen neto
        4. Margen operacional
        5. Margen bruto
        6. Rentabilidad vs competencia del sector
        
        Evalúa tendencias y sostenibilidad de la rentabilidad.
        Responde en formato JSON con análisis detallado.
        """
        
        try:
            logger.info("🔄 Solicitando análisis de rentabilidad a OpenAI...")
            response = await self.openai_service.generar_respuesta_json(prompt)
            
            logger.debug(f"📥 Respuesta de OpenAI recibida: {response[:200]}...")
            
            # Verificar que la respuesta no esté vacía
            if not response or response.strip() == "":
                logger.error("❌ Respuesta vacía de OpenAI")
                return {
                    "categoria": "rentabilidad",
                    "resultado": {
                        "indicadores": {},
                        "analisis": "No se pudo realizar el análisis por falta de respuesta del modelo",
                        "nivel_rentabilidad": "MEDIO",
                        "observaciones": ["Error en análisis automático"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            analisis = json.loads(response)
            
            # Verificar si hay error en la respuesta
            if "error" in analisis:
                logger.error(f"Error en respuesta de análisis de rentabilidad: {analisis['error']}")
                return {
                    "categoria": "rentabilidad",
                    "resultado": {
                        "indicadores": {},
                        "analisis": f"Error en análisis: {analisis.get('error', 'Desconocido')}",
                        "nivel_rentabilidad": "MEDIO",
                        "observaciones": ["Error en procesamiento"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.success("✅ Análisis de rentabilidad completado")
            return {
                "categoria": "rentabilidad",
                "resultado": analisis,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON en análisis de rentabilidad: {str(e)}")
            logger.debug(f"Respuesta que causó error: {response if 'response' in locals() else 'N/A'}")
            return {
                "categoria": "rentabilidad",
                "resultado": {
                    "indicadores": {},
                    "analisis": "Error en formato de respuesta del modelo de IA",
                    "nivel_rentabilidad": "MEDIO",
                    "observaciones": ["Respuesta inválida del modelo"]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en análisis de rentabilidad: {str(e)}")
            return {
                "categoria": "rentabilidad",
                "resultado": {
                    "indicadores": {},
                    "analisis": f"Error técnico: {str(e)}",
                    "nivel_rentabilidad": "MEDIO",
                    "observaciones": ["Error en procesamiento"]
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analizar_eficiencia(self, datos: Dict) -> Dict:
        """Analiza los indicadores de eficiencia operativa."""
        prompt = f"""
        Analiza la eficiencia operativa de {datos['empresa']['nombre']}.
        
        Información:
        - Sector: {datos['empresa']['sector']}
        - Estado financiero: {datos['contenido_extraido'][:1500]}
        
        Evalúa:
        1. Rotación de activos
        2. Rotación de inventarios
        3. Periodo promedio de cobro
        4. Periodo promedio de pago
        5. Ciclo de conversión de efectivo
        6. Eficiencia en el uso de recursos
        
        Compara con estándares del sector y proporciona recomendaciones.
        Responde en formato JSON.
        """
        
        try:
            logger.info("🔄 Solicitando análisis de eficiencia a OpenAI...")
            response = await self.openai_service.generar_respuesta_json(prompt)
            
            logger.debug(f"📥 Respuesta de OpenAI recibida: {response[:200]}...")
            
            # Verificar que la respuesta no esté vacía
            if not response or response.strip() == "":
                logger.error("❌ Respuesta vacía de OpenAI")
                return {
                    "categoria": "eficiencia",
                    "resultado": {
                        "indicadores": {},
                        "evaluacion": "No se pudo realizar el análisis por falta de respuesta del modelo",
                        "nivel_eficiencia": "MEDIO",
                        "recomendaciones": ["Error en análisis automático"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            analisis = json.loads(response)
            
            # Verificar si hay error en la respuesta
            if "error" in analisis:
                logger.error(f"Error en respuesta de análisis de eficiencia: {analisis['error']}")
                return {
                    "categoria": "eficiencia",
                    "resultado": {
                        "indicadores": {},
                        "evaluacion": f"Error en análisis: {analisis.get('error', 'Desconocido')}",
                        "nivel_eficiencia": "MEDIO",
                        "recomendaciones": ["Error en procesamiento"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.success("✅ Análisis de eficiencia completado")
            return {
                "categoria": "eficiencia",
                "resultado": analisis,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON en análisis de eficiencia: {str(e)}")
            logger.debug(f"Respuesta que causó error: {response if 'response' in locals() else 'N/A'}")
            return {
                "categoria": "eficiencia",
                "resultado": {
                    "indicadores": {},
                    "evaluacion": "Error en formato de respuesta del modelo de IA",
                    "nivel_eficiencia": "MEDIO",
                    "recomendaciones": ["Respuesta inválida del modelo"]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en análisis de eficiencia: {str(e)}")
            return {
                "categoria": "eficiencia",
                "resultado": {
                    "indicadores": {},
                    "evaluacion": f"Error técnico: {str(e)}",
                    "nivel_eficiencia": "MEDIO",
                    "recomendaciones": ["Error en procesamiento"]
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analizar_riesgo_sectorial(self, datos: Dict) -> Dict:
        """Analiza riesgos específicos del sector."""
        prompt = f"""
        Como analista senior especializado, evalúa los riesgos específicos del sector 
        {datos['empresa']['sector']} para la empresa {datos['empresa']['nombre']}.
        
        Considera:
        1. Riesgos regulatorios del sector
        2. Ciclos económicos que afectan al sector
        3. Competencia y concentración del mercado
        4. Barreras de entrada y salida
        5. Dependencia de factores externos
        6. Innovación tecnológica y disrupciones
        7. Sostenibilidad y responsabilidad social
        
        Evalúa cómo estos riesgos impactan específicamente a esta empresa.
        Responde en formato JSON con análisis detallado.
        """
        
        try:
            logger.info("🔄 Solicitando análisis de riesgo sectorial a OpenAI...")
            response = await self.openai_service.generar_respuesta_json(prompt)
            
            logger.debug(f"📥 Respuesta de OpenAI recibida: {response[:200]}...")
            
            # Verificar que la respuesta no esté vacía
            if not response or response.strip() == "":
                logger.error("❌ Respuesta vacía de OpenAI")
                return {
                    "categoria": "sectorial",
                    "resultado": {
                        "riesgos_identificados": [],
                        "evaluacion": "No se pudo realizar el análisis por falta de respuesta del modelo",
                        "nivel_riesgo": "MEDIO",
                        "mitigaciones": ["Error en análisis automático"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            analisis = json.loads(response)
            
            # Verificar si hay error en la respuesta
            if "error" in analisis:
                logger.error(f"Error en respuesta de análisis sectorial: {analisis['error']}")
                return {
                    "categoria": "sectorial",
                    "resultado": {
                        "riesgos_identificados": [],
                        "evaluacion": f"Error en análisis: {analisis.get('error', 'Desconocido')}",
                        "nivel_riesgo": "MEDIO",
                        "mitigaciones": ["Error en procesamiento"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.success("✅ Análisis sectorial completado")
            return {
                "categoria": "sectorial",
                "resultado": analisis,
                "timestamp": datetime.now().isoformat()
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON en análisis sectorial: {str(e)}")
            logger.debug(f"Respuesta que causó error: {response if 'response' in locals() else 'N/A'}")
            return {
                "categoria": "sectorial",
                "resultado": {
                    "riesgos_identificados": [],
                    "evaluacion": "Error en formato de respuesta del modelo de IA",
                    "nivel_riesgo": "MEDIO",
                    "mitigaciones": ["Respuesta inválida del modelo"]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en análisis sectorial: {str(e)}")
            return {
                "categoria": "sectorial",
                "resultado": {
                    "riesgos_identificados": [],
                    "evaluacion": f"Error técnico: {str(e)}",
                    "nivel_riesgo": "MEDIO",
                    "mitigaciones": ["Error en procesamiento"]
                },
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generar_calificacion_riesgo(self, analisis_resultados: Dict) -> Dict:
        """Genera la calificación de riesgo global."""
        prompt = f"""
        Como analista senior de riesgos, basándote en los siguientes análisis:
        
        LIQUIDEZ: {analisis_resultados.get('liquidez', {})}
        SOLVENCIA: {analisis_resultados.get('solvencia', {})}
        RENTABILIDAD: {analisis_resultados.get('rentabilidad', {})}
        EFICIENCIA: {analisis_resultados.get('eficiencia', {})}
        SECTORIAL: {analisis_resultados.get('sectorial', {})}
        
        Determina una calificación de riesgo global:
        - BASICO: Riesgo bajo, empresa sólida, aprobación puede ser automática o con revisión mínima
        - INTERMEDIO: Riesgo moderado, requiere análisis humano adicional
        - AVANZADO: Riesgo alto, requiere análisis exhaustivo por especialista senior
        
        Proporciona:
        1. Nivel de riesgo (BASICO/INTERMEDIO/AVANZADO)
        2. Puntuación numérica (1-100)
        3. Factores determinantes
        4. Justificación detallada
        
        Responde en formato JSON.
        """
        
        try:
            logger.info("🔄 Solicitando calificación de riesgo global a OpenAI...")
            response = await self.openai_service.generar_respuesta_json(prompt)
            
            logger.debug(f"📥 Respuesta de OpenAI recibida: {response[:200]}...")
            
            # Verificar que la respuesta no esté vacía
            if not response or response.strip() == "":
                logger.error("❌ Respuesta vacía de OpenAI")
                return {
                    "nivel": settings.DEFAULT_RISK_LEVEL,
                    "puntuacion": 50,
                    "factores": ["Error: No se pudo generar calificación"],
                    "justificacion": "No se pudo completar la evaluación por falta de respuesta del modelo"
                }
            
            calificacion = json.loads(response)
            
            # Verificar si hay error en la respuesta
            if "error" in calificacion:
                logger.error(f"Error en respuesta de calificación: {calificacion['error']}")
                return {
                    "nivel": settings.DEFAULT_RISK_LEVEL,
                    "puntuacion": 50,
                    "factores": ["Error en procesamiento"],
                    "justificacion": f"Error en análisis: {calificacion.get('error', 'Desconocido')}"
                }
            
            logger.success("✅ Calificación de riesgo completada")
            return calificacion
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON en calificación: {str(e)}")
            logger.debug(f"Respuesta que causó error: {response if 'response' in locals() else 'N/A'}")
            return {
                "nivel": settings.DEFAULT_RISK_LEVEL,
                "puntuacion": 50,
                "factores": ["Error de formato"],
                "justificacion": "Error en formato de respuesta del modelo"
            }
        except Exception as e:
            logger.error(f"Error generando calificación: {str(e)}")
            return {
                "nivel": settings.DEFAULT_RISK_LEVEL,
                "puntuacion": 50,
                "factores": ["Error en análisis automático"],
                "justificacion": f"Error en el proceso: {str(e)}"
            }
    
    async def _generar_recomendaciones(self, calificacion: Dict, analisis: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        prompt = f"""
        Basándote en la calificación de riesgo {calificacion} y el análisis detallado,
        genera recomendaciones específicas y accionables para:
        
        1. Mitigación de riesgos identificados
        2. Mejoras en la gestión financiera
        3. Aspectos a monitorear
        4. Acciones correctivas sugeridas
        5. Oportunidades de mejora
        
        Proporciona entre 5-10 recomendaciones concretas.
        Responde como lista de strings en formato JSON.
        """
        
        try:
            logger.info("🔄 Solicitando generación de recomendaciones a OpenAI...")
            response = await self.openai_service.generar_respuesta_json(prompt)
            
            logger.debug(f"📥 Respuesta de OpenAI recibida: {response[:200]}...")
            
            # Verificar que la respuesta no esté vacía
            if not response or response.strip() == "":
                logger.error("❌ Respuesta vacía de OpenAI")
                return [
                    "Revisar estados financieros detalladamente",
                    "Monitorear indicadores clave de liquidez",
                    "Evaluar estructura de capital",
                    "Verificar flujos de efectivo",
                    "Analizar rentabilidad operativa"
                ]
            
            recomendaciones = json.loads(response)
            
            # Verificar si hay error en la respuesta
            if isinstance(recomendaciones, dict) and "error" in recomendaciones:
                logger.error(f"Error en respuesta de recomendaciones: {recomendaciones['error']}")
                return [
                    "Revisar estados financieros detalladamente",
                    "Monitorear indicadores clave",
                    "Consultar con analista especializado"
                ]
            
            logger.success("✅ Recomendaciones generadas")
            return recomendaciones if isinstance(recomendaciones, list) else [str(recomendaciones)]
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON en recomendaciones: {str(e)}")
            logger.debug(f"Respuesta que causó error: {response if 'response' in locals() else 'N/A'}")
            return [
                "Revisar estados financieros",
                "Monitorear indicadores clave",
                "Evaluar riesgos identificados"
            ]
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return [
                "Revisar estados financieros",
                "Monitorear indicadores clave"
            ]
    
    def _determinar_perfil_aprobador(self, calificacion: Dict) -> Dict:
        """Determina qué perfil humano debe aprobar según el riesgo."""
        nivel = calificacion.get("nivel", "INTERMEDIO")
        
        perfiles = {
            "BASICO": {
                "perfil": "Analista Junior",
                "experiencia_minima": "1-2 años",
                "especialidad": "Análisis básico de estados financieros",
                "autoridad": "Hasta $100,000 USD",
                "supervision": "Revisión por muestreo"
            },
            "INTERMEDIO": {
                "perfil": "Analista Senior",
                "experiencia_minima": "3-5 años",
                "especialidad": "Análisis de riesgos y evaluación financiera",
                "autoridad": "Hasta $500,000 USD",
                "supervision": "Revisión por analista principal"
            },
            "AVANZADO": {
                "perfil": "Especialista en Riesgos / Gerente",
                "experiencia_minima": "5+ años",
                "especialidad": "Análisis complejo de riesgos y decisiones estratégicas",
                "autoridad": "Sin límite o comité de riesgos",
                "supervision": "Revisión por comité ejecutivo"
            }
        }
        
        return perfiles.get(nivel, perfiles["INTERMEDIO"])
    
    async def _generar_resumen_ejecutivo(self, analisis: Dict, calificacion: Dict) -> str:
        """Genera un resumen ejecutivo del análisis."""
        prompt = f"""
        Genera un resumen ejecutivo profesional basado en:
        
        CALIFICACIÓN: {calificacion}
        ANÁLISIS DETALLADO: {analisis}
        
        El resumen debe:
        1. Ser conciso (máximo 300 palabras)
        2. Destacar los puntos clave
        3. Incluir la recomendación final
        4. Ser comprensible para ejecutivos
        5. Mencionar los principales riesgos y fortalezas
        
        Escribe en tono profesional y directo.
        """
        
        try:
            response = await self.openai_service.generar_respuesta(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generando resumen: {str(e)}")
            return "Resumen no disponible debido a error en el procesamiento."
    
    async def _guardar_analisis(self, session_id: str, reporte: Dict) -> None:
        """Guarda el análisis completo en archivo JSON."""
        archivo_analisis = Path(settings.OUTPUT_DIR) / f"{session_id}_analisis_completo.json"
        
        try:
            with open(archivo_analisis, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Análisis guardado: {archivo_analisis}")
        except Exception as e:
            logger.error(f"Error guardando análisis: {str(e)}")
    
    async def generar_documento_final(self, session_id: str) -> Dict:
        """
        Genera el documento PDF final con el análisis completo.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Dict con información del documento generado
        """
        try:
            # Cargar análisis completo
            archivo_analisis = Path(settings.OUTPUT_DIR) / f"{session_id}_analisis_completo.json"
            
            if not archivo_analisis.exists():
                return {"error": "Análisis no encontrado"}
            
            with open(archivo_analisis, 'r', encoding='utf-8') as f:
                reporte = json.load(f)
            
            # Generar PDF
            pdf_path = await self.report_generator.generar_reporte_pdf(reporte, session_id)
            
            logger.info(f"📄 Documento PDF generado: {pdf_path}")
            
            return {
                "success": True,
                "pdf_path": pdf_path,
                "reporte": reporte,
                "mensaje": "Análisis financiero completado y documento generado exitosamente."
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando documento final: {str(e)}")
            return {"error": f"Error generando documento: {str(e)}"}