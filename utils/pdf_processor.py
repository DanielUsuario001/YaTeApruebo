"""
Procesador de archivos PDF.
Extrae y procesa contenido de documentos financieros.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import PyPDF2
from datetime import datetime

from config.settings import settings
from loguru import logger

class PDFProcessor:
    """
    Procesador especializado para archivos PDF financieros.
    
    Funcionalidades:
    - Extracción inteligente de texto
    - Identificación de tablas financieras
    - Limpieza y estructuración de datos
    - Detección de indicadores clave
    """
    
    def __init__(self):
        """Inicializa el procesador PDF."""
        # Patrones para identificar secciones financieras
        self.patrones_financieros = {
            "balance_general": [
                r"balance\s+general", r"estado\s+de\s+situación", r"situación\s+financiera",
                r"balance\s+sheet", r"statement\s+of\s+financial\s+position"
            ],
            "estado_resultados": [
                r"estado\s+de\s+resultados", r"estado\s+de\s+pérdidas\s+y\s+ganancias",
                r"income\s+statement", r"profit\s+and\s+loss", r"p&l"
            ],
            "flujo_efectivo": [
                r"flujo\s+de\s+efectivo", r"cash\s+flow", r"estado\s+de\s+flujos"
            ],
            "patrimonio": [
                r"estado\s+de\s+patrimonio", r"cambios\s+en\s+el\s+patrimonio",
                r"statement\s+of\s+equity", r"changes\s+in\s+equity"
            ]
        }
        
        # Patrones para identificar cifras monetarias
        self.patron_monetario = re.compile(
            r'[\$\€\£]?\s*[\d,]+\.?\d*\s*(?:millones?|millions?|miles?|thousands?|k|m|mm)?',
            re.IGNORECASE
        )
        
        logger.info("📄 Procesador PDF inicializado")
    
    async def procesar_pdf_completo(self, archivo_path: str) -> Dict:
        """
        Procesa completamente un archivo PDF financiero.
        
        Args:
            archivo_path: Ruta del archivo PDF
            
        Returns:
            Dict con información procesada del PDF
        """
        try:
            archivo = Path(archivo_path)
            
            if not archivo.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {archivo_path}")
            
            logger.info(f"📖 Procesando PDF: {archivo.name}")
            
            # Extraer texto completo
            texto_completo = await self._extraer_texto_completo(archivo_path)
            
            # Identificar secciones financieras
            secciones = await self._identificar_secciones_financieras(texto_completo)
            
            # Extraer indicadores clave
            indicadores = await self._extraer_indicadores_clave(texto_completo)
            
            # Detectar tablas financieras
            tablas = await self._detectar_tablas_financieras(texto_completo)
            
            # Generar resumen del documento
            resumen = await self._generar_resumen_documento(texto_completo, secciones)
            
            resultado = {
                "archivo": archivo.name,
                "fecha_procesamiento": datetime.now().isoformat(),
                "estadisticas": {
                    "num_paginas": len(texto_completo.split("--- PÁGINA")),
                    "caracteres_totales": len(texto_completo),
                    "palabras_totales": len(texto_completo.split()),
                },
                "contenido": {
                    "texto_completo": texto_completo,
                    "secciones_identificadas": secciones,
                    "indicadores_clave": indicadores,
                    "tablas_detectadas": tablas,
                    "resumen": resumen
                },
                "calidad_extraccion": await self._evaluar_calidad_extraccion(texto_completo)
            }
            
            logger.info(f"✅ PDF procesado exitosamente: {archivo.name}")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF: {str(e)}")
            raise Exception(f"Error procesando PDF: {str(e)}")
    
    async def _extraer_texto_completo(self, archivo_path: str) -> str:
        """Extrae todo el texto del PDF con metadatos de página."""
        try:
            with open(archivo_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                texto_completo = ""
                
                for num_pagina, pagina in enumerate(pdf_reader.pages):
                    try:
                        texto_pagina = pagina.extract_text()
                        
                        # Limpiar texto de la página
                        texto_limpio = self._limpiar_texto_pagina(texto_pagina)
                        
                        if texto_limpio.strip():
                            texto_completo += f"\n=== PÁGINA {num_pagina + 1} ===\n"
                            texto_completo += texto_limpio
                            texto_completo += "\n"
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error extrayendo página {num_pagina + 1}: {str(e)}")
                        continue
                
                return texto_completo
                
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto: {str(e)}")
            raise
    
    def _limpiar_texto_pagina(self, texto: str) -> str:
        """Limpia el texto extraído de una página."""
        if not texto:
            return ""
        
        # Eliminar caracteres de control
        texto_limpio = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)
        
        # Normalizar espacios y saltos de línea
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        texto_limpio = re.sub(r'\n\s*\n', '\n', texto_limpio)
        
        # Eliminar líneas muy cortas (probablemente ruido)
        lineas = texto_limpio.split('\n')
        lineas_filtradas = []
        
        for linea in lineas:
            linea = linea.strip()
            if len(linea) > 2:  # Solo líneas con más de 2 caracteres
                lineas_filtradas.append(linea)
        
        return '\n'.join(lineas_filtradas)
    
    async def _identificar_secciones_financieras(self, texto: str) -> Dict:
        """Identifica las diferentes secciones financieras en el texto."""
        secciones_encontradas = {}
        texto_lower = texto.lower()
        
        for seccion, patrones in self.patrones_financieros.items():
            for patron in patrones:
                matches = list(re.finditer(patron, texto_lower))
                if matches:
                    secciones_encontradas[seccion] = {
                        "encontrada": True,
                        "posiciones": [m.start() for m in matches],
                        "patron_usado": patron,
                        "num_menciones": len(matches)
                    }
                    break
            
            if seccion not in secciones_encontradas:
                secciones_encontradas[seccion] = {
                    "encontrada": False,
                    "posiciones": [],
                    "patron_usado": None,
                    "num_menciones": 0
                }
        
        logger.debug(f"📊 Secciones identificadas: {list(secciones_encontradas.keys())}")
        return secciones_encontradas
    
    async def _extraer_indicadores_clave(self, texto: str) -> Dict:
        """Extrae indicadores financieros clave del texto."""
        indicadores = {
            "cifras_monetarias": [],
            "porcentajes": [],
            "fechas": [],
            "ratios": []
        }
        
        # Extraer cifras monetarias
        cifras_monetarias = self.patron_monetario.findall(texto)
        indicadores["cifras_monetarias"] = list(set(cifras_monetarias))[:20]  # Limitar a 20
        
        # Extraer porcentajes
        patron_porcentajes = re.compile(r'\d+\.?\d*\s*%')
        porcentajes = patron_porcentajes.findall(texto)
        indicadores["porcentajes"] = list(set(porcentajes))[:15]
        
        # Extraer fechas
        patron_fechas = re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}')
        fechas = patron_fechas.findall(texto)
        indicadores["fechas"] = list(set(fechas))[:10]
        
        # Buscar ratios comunes
        patrones_ratios = [
            r'ratio\s+corriente\s*:?\s*[\d,\.]+',
            r'roa\s*:?\s*[\d,\.]+\s*%?',
            r'roe\s*:?\s*[\d,\.]+\s*%?',
            r'margen\s+neto\s*:?\s*[\d,\.]+\s*%?',
            r'endeudamiento\s*:?\s*[\d,\.]+\s*%?'
        ]
        
        for patron in patrones_ratios:
            matches = re.findall(patron, texto, re.IGNORECASE)
            indicadores["ratios"].extend(matches)
        
        indicadores["ratios"] = list(set(indicadores["ratios"]))[:10]
        
        return indicadores
    
    async def _detectar_tablas_financieras(self, texto: str) -> List[Dict]:
        """Detecta posibles tablas financieras en el texto."""
        tablas_detectadas = []
        
        # Dividir por páginas
        paginas = texto.split("=== PÁGINA")
        
        for i, pagina in enumerate(paginas):
            if not pagina.strip():
                continue
            
            # Buscar patrones de tabla (líneas con múltiples números/cifras)
            lineas = pagina.split('\n')
            tabla_actual = []
            
            for linea in lineas:
                # Contar cifras monetarias y números en la línea
                cifras = len(self.patron_monetario.findall(linea))
                numeros = len(re.findall(r'\d+', linea))
                
                # Si tiene suficientes números, podría ser parte de una tabla
                if cifras >= 2 or numeros >= 3:
                    tabla_actual.append(linea.strip())
                else:
                    # Si la tabla actual tiene suficientes filas, guardarla
                    if len(tabla_actual) >= 3:
                        tablas_detectadas.append({
                            "pagina": i + 1,
                            "filas": tabla_actual.copy(),
                            "num_filas": len(tabla_actual),
                            "contenido_muestra": tabla_actual[0][:100] if tabla_actual else ""
                        })
                    tabla_actual = []
            
            # Verificar tabla al final de la página
            if len(tabla_actual) >= 3:
                tablas_detectadas.append({
                    "pagina": i + 1,
                    "filas": tabla_actual.copy(),
                    "num_filas": len(tabla_actual),
                    "contenido_muestra": tabla_actual[0][:100] if tabla_actual else ""
                })
        
        logger.debug(f"📋 Tablas detectadas: {len(tablas_detectadas)}")
        return tablas_detectadas[:10]  # Limitar a 10 tablas
    
    async def _generar_resumen_documento(self, texto: str, secciones: Dict) -> Dict:
        """Genera un resumen del documento financiero."""
        palabras = texto.split()
        num_palabras = len(palabras)
        
        # Calcular densidad de información financiera
        cifras_monetarias = len(self.patron_monetario.findall(texto))
        densidad_financiera = cifras_monetarias / max(num_palabras, 1) * 1000  # Por cada 1000 palabras
        
        # Identificar palabras clave financieras
        palabras_clave_financieras = [
            "activo", "pasivo", "patrimonio", "ingresos", "gastos", "utilidad",
            "pérdida", "efectivo", "inventario", "cuentas por cobrar", "deuda",
            "capital", "dividendos", "depreciación", "amortización"
        ]
        
        frecuencia_palabras_clave = {}
        texto_lower = texto.lower()
        
        for palabra in palabras_clave_financieras:
            frecuencia = len(re.findall(r'\b' + palabra + r'\b', texto_lower))
            if frecuencia > 0:
                frecuencia_palabras_clave[palabra] = frecuencia
        
        resumen = {
            "num_palabras": num_palabras,
            "num_caracteres": len(texto),
            "densidad_financiera": round(densidad_financiera, 2),
            "secciones_presentes": [k for k, v in secciones.items() if v["encontrada"]],
            "num_secciones_encontradas": sum(1 for v in secciones.values() if v["encontrada"]),
            "palabras_clave_frecuencia": frecuencia_palabras_clave,
            "calidad_contenido": self._evaluar_calidad_contenido(num_palabras, cifras_monetarias)
        }
        
        return resumen
    
    def _evaluar_calidad_contenido(self, num_palabras: int, cifras_monetarias: int) -> str:
        """Evalúa la calidad del contenido extraído."""
        if num_palabras < 100:
            return "BAJA"
        elif num_palabras < 500:
            return "REGULAR"
        elif cifras_monetarias < 5:
            return "REGULAR"
        elif num_palabras > 1000 and cifras_monetarias > 10:
            return "ALTA"
        else:
            return "BUENA"
    
    async def _evaluar_calidad_extraccion(self, texto: str) -> Dict:
        """Evalúa la calidad de la extracción de texto."""
        if not texto:
            return {
                "calidad": "MALA",
                "puntuacion": 0,
                "problemas": ["Texto vacío"]
            }
        
        problemas = []
        puntuacion = 100
        
        # Verificar longitud mínima
        if len(texto) < 500:
            problemas.append("Texto muy corto")
            puntuacion -= 30
        
        # Verificar proporción de caracteres especiales
        caracteres_especiales = len(re.findall(r'[^\w\s\.,\-\(\)\%\$]', texto))
        proporcion_especiales = caracteres_especiales / max(len(texto), 1)
        
        if proporcion_especiales > 0.1:
            problemas.append("Muchos caracteres especiales (posible OCR deficiente)")
            puntuacion -= 20
        
        # Verificar presencia de números/cifras
        numeros = len(re.findall(r'\d', texto))
        proporcion_numeros = numeros / max(len(texto), 1)
        
        if proporcion_numeros < 0.05:
            problemas.append("Pocos números detectados")
            puntuacion -= 25
        
        # Verificar palabras financieras
        palabras_financieras = len(re.findall(
            r'\b(activo|pasivo|patrimonio|ingresos|gastos|utilidad)\b', 
            texto.lower()
        ))
        
        if palabras_financieras < 3:
            problemas.append("Pocas palabras financieras detectadas")
            puntuacion -= 15
        
        # Determinar calidad final
        if puntuacion >= 85:
            calidad = "EXCELENTE"
        elif puntuacion >= 70:
            calidad = "BUENA"
        elif puntuacion >= 50:
            calidad = "REGULAR"
        else:
            calidad = "MALA"
        
        return {
            "calidad": calidad,
            "puntuacion": max(puntuacion, 0),
            "problemas": problemas,
            "metricas": {
                "longitud_texto": len(texto),
                "proporcion_especiales": round(proporcion_especiales, 4),
                "proporcion_numeros": round(proporcion_numeros, 4),
                "palabras_financieras": palabras_financieras
            }
        }
    
    async def extraer_seccion_especifica(self, archivo_path: str, tipo_seccion: str) -> Optional[str]:
        """
        Extrae una sección específica del PDF.
        
        Args:
            archivo_path: Ruta del archivo PDF
            tipo_seccion: Tipo de sección a extraer
            
        Returns:
            Texto de la sección o None si no se encuentra
        """
        try:
            texto_completo = await self._extraer_texto_completo(archivo_path)
            secciones = await self._identificar_secciones_financieras(texto_completo)
            
            if tipo_seccion not in secciones or not secciones[tipo_seccion]["encontrada"]:
                return None
            
            posiciones = secciones[tipo_seccion]["posiciones"]
            if not posiciones:
                return None
            
            # Extraer texto desde la primera posición encontrada
            inicio = posiciones[0]
            
            # Buscar el final de la sección (siguiente sección o final del texto)
            fin = len(texto_completo)
            for seccion, info in secciones.items():
                if seccion != tipo_seccion and info["encontrada"]:
                    for pos in info["posiciones"]:
                        if pos > inicio and pos < fin:
                            fin = pos
            
            seccion_texto = texto_completo[inicio:fin]
            return seccion_texto[:5000]  # Limitar a 5000 caracteres
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo sección {tipo_seccion}: {str(e)}")
            return None