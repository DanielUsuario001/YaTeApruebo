"""
Servicio de gestión de archivos.
Maneja la carga, validación y procesamiento de archivos PDF.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional
import PyPDF2
from datetime import datetime

from config.settings import settings
from loguru import logger

class FileService:
    """
    Servicio para gestión de archivos del sistema YaTeApruebo.
    
    Funciones principales:
    - Validación de archivos PDF
    - Almacenamiento seguro de archivos
    - Extracción de texto de PDFs
    - Gestión de directorios
    """
    
    def __init__(self):
        """Inicializa el servicio de archivos."""
        self.input_dir = Path(settings.INPUT_DIR)
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.logs_dir = Path(settings.LOGS_DIR)
        
        # Crear directorios si no existen
        self._crear_directorios()
        
        logger.info("📁 Servicio de archivos inicializado")
    
    def _crear_directorios(self) -> None:
        """Crea los directorios necesarios si no existen."""
        for directory in [self.input_dir, self.output_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.debug("📂 Directorios verificados/creados")
    
    async def validar_archivo_pdf(self, archivo_path: str) -> Dict:
        """
        Valida que el archivo sea un PDF válido y cumpla los requisitos.
        
        Args:
            archivo_path: Ruta del archivo a validar
            
        Returns:
            Dict con resultado de la validación
        """
        try:
            archivo = Path(archivo_path)
            
            # Verificar que el archivo existe
            if not archivo.exists():
                return {
                    "valido": False,
                    "razon": "El archivo no existe"
                }
            
            # Verificar extensión
            if archivo.suffix.lower() != '.pdf':
                return {
                    "valido": False,
                    "razon": "El archivo debe ser un PDF"
                }
            
            # Verificar tamaño
            tamaño_archivo = archivo.stat().st_size
            if tamaño_archivo > settings.MAX_FILE_SIZE:
                tamaño_mb = tamaño_archivo / (1024 * 1024)
                limite_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                return {
                    "valido": False,
                    "razon": f"Archivo muy grande ({tamaño_mb:.1f}MB). Límite: {limite_mb:.1f}MB"
                }
            
            # Verificar que es un PDF válido
            try:
                with open(archivo_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    num_paginas = len(pdf_reader.pages)
                    
                    if num_paginas == 0:
                        return {
                            "valido": False,
                            "razon": "El PDF no contiene páginas"
                        }
                    
                    # Verificar que se puede extraer texto
                    primera_pagina = pdf_reader.pages[0]
                    texto_muestra = primera_pagina.extract_text()
                    
                    if len(texto_muestra.strip()) < 10:
                        return {
                            "valido": False,
                            "razon": "El PDF no contiene texto extraíble (posiblemente escaneado)"
                        }
                        
            except Exception as e:
                return {
                    "valido": False,
                    "razon": f"Error leyendo PDF: {str(e)}"
                }
            
            logger.info(f"✅ Archivo PDF validado: {archivo.name} ({num_paginas} páginas)")
            
            return {
                "valido": True,
                "archivo": archivo.name,
                "tamaño": tamaño_archivo,
                "num_paginas": num_paginas,
                "ruta": str(archivo)
            }
            
        except Exception as e:
            logger.error(f"❌ Error validando archivo: {str(e)}")
            return {
                "valido": False,
                "razon": f"Error inesperado: {str(e)}"
            }
    
    async def guardar_archivo_input(
        self, 
        archivo_path: str, 
        session_id: str,
        nombre_empresa: str
    ) -> Dict:
        """
        Guarda el archivo en el directorio de input con nombre estandarizado.
        
        Args:
            archivo_path: Ruta del archivo original
            session_id: ID de la sesión
            nombre_empresa: Nombre de la empresa
            
        Returns:
            Dict con información del archivo guardado
        """
        try:
            archivo_original = Path(archivo_path)
            
            # Generar nombre estandarizado
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_empresa_limpio = self._limpiar_nombre(nombre_empresa)
            nuevo_nombre = f"{session_id}_{nombre_empresa_limpio}_{timestamp}.pdf"
            
            # Ruta de destino
            ruta_destino = self.input_dir / nuevo_nombre
            
            # Copiar archivo
            shutil.copy2(archivo_original, ruta_destino)
            
            # Verificar que se copió correctamente
            if not ruta_destino.exists():
                raise Exception("Error copiando archivo")
            
            tamaño = ruta_destino.stat().st_size
            
            logger.info(f"💾 Archivo guardado: {nuevo_nombre}")
            
            return {
                "success": True,
                "path": str(ruta_destino),
                "nombre": nuevo_nombre,
                "tamaño": tamaño,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Error guardando archivo: {str(e)}")
            return {
                "success": False,
                "error": f"Error guardando archivo: {str(e)}"
            }
    
    async def extraer_texto_pdf(self, archivo_path: str) -> str:
        """
        Extrae todo el texto de un archivo PDF.
        
        Args:
            archivo_path: Ruta del archivo PDF
            
        Returns:
            Texto extraído del PDF
            
        Raises:
            Exception: Si hay error extrayendo el texto
        """
        try:
            with open(archivo_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                texto_completo = ""
                
                for num_pagina, pagina in enumerate(pdf_reader.pages):
                    try:
                        texto_pagina = pagina.extract_text()
                        texto_completo += f"\n--- PÁGINA {num_pagina + 1} ---\n"
                        texto_completo += texto_pagina
                        texto_completo += "\n"
                    except Exception as e:
                        logger.warning(f"⚠️ Error extrayendo página {num_pagina + 1}: {str(e)}")
                        continue
                
                # Limpiar texto
                texto_limpio = self._limpiar_texto(texto_completo)
                
                logger.info(f"📖 Texto extraído: {len(texto_limpio)} caracteres")
                
                return texto_limpio
                
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto del PDF: {str(e)}")
            raise Exception(f"Error procesando PDF: {str(e)}")
    
    def _limpiar_nombre(self, nombre: str) -> str:
        """Limpia un nombre para usar como nombre de archivo."""
        # Caracteres permitidos: letras, números, guiones y guiones bajos
        caracteres_validos = ""
        for char in nombre:
            if char.isalnum() or char in "-_":
                caracteres_validos += char
            elif char.isspace():
                caracteres_validos += "_"
        
        # Limitar longitud
        return caracteres_validos[:50]
    
    def _limpiar_texto(self, texto: str) -> str:
        """Limpia el texto extraído del PDF."""
        # Eliminar líneas vacías múltiples
        lineas = texto.split('\n')
        lineas_limpias = []
        
        for linea in lineas:
            linea_limpia = linea.strip()
            if linea_limpia:  # Solo agregar líneas no vacías
                lineas_limpias.append(linea_limpia)
        
        texto_limpio = '\n'.join(lineas_limpias)
        
        # Limitar texto si es muy largo (para evitar exceder límites de tokens)
        if len(texto_limpio) > 50000:  # ~50k caracteres
            logger.warning("⚠️ Texto muy largo, truncando para análisis")
            texto_limpio = texto_limpio[:50000] + "\n\n[... TEXTO TRUNCADO ...]"
        
        return texto_limpio
    
    async def crear_archivo_output(
        self, 
        contenido: str, 
        nombre_archivo: str,
        extension: str = "txt"
    ) -> Dict:
        """
        Crea un archivo en el directorio de output.
        
        Args:
            contenido: Contenido del archivo
            nombre_archivo: Nombre base del archivo
            extension: Extensión del archivo
            
        Returns:
            Dict con información del archivo creado
        """
        try:
            # Generar nombre completo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_completo = f"{nombre_archivo}_{timestamp}.{extension}"
            ruta_archivo = self.output_dir / nombre_completo
            
            # Escribir archivo
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            tamaño = ruta_archivo.stat().st_size
            
            logger.info(f"📝 Archivo output creado: {nombre_completo}")
            
            return {
                "success": True,
                "path": str(ruta_archivo),
                "nombre": nombre_completo,
                "tamaño": tamaño
            }
            
        except Exception as e:
            logger.error(f"❌ Error creando archivo output: {str(e)}")
            return {
                "success": False,
                "error": f"Error creando archivo: {str(e)}"
            }
    
    def listar_archivos_input(self) -> list:
        """Lista todos los archivos en el directorio input."""
        try:
            archivos = []
            for archivo in self.input_dir.glob("*.pdf"):
                stat = archivo.stat()
                archivos.append({
                    "nombre": archivo.name,
                    "path": str(archivo),
                    "tamaño": stat.st_size,
                    "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return archivos
        except Exception as e:
            logger.error(f"❌ Error listando archivos input: {str(e)}")
            return []
    
    def listar_archivos_output(self) -> list:
        """Lista todos los archivos en el directorio output."""
        try:
            archivos = []
            for archivo in self.output_dir.glob("*"):
                if archivo.is_file():
                    stat = archivo.stat()
                    archivos.append({
                        "nombre": archivo.name,
                        "path": str(archivo),
                        "tamaño": stat.st_size,
                        "extension": archivo.suffix,
                        "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return archivos
        except Exception as e:
            logger.error(f"❌ Error listando archivos output: {str(e)}")
            return []
    
    def eliminar_archivo(self, archivo_path: str) -> Dict:
        """
        Elimina un archivo específico.
        
        Args:
            archivo_path: Ruta del archivo a eliminar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            archivo = Path(archivo_path)
            
            if not archivo.exists():
                return {
                    "success": False,
                    "error": "Archivo no encontrado"
                }
            
            archivo.unlink()
            
            logger.info(f"🗑️ Archivo eliminado: {archivo.name}")
            
            return {
                "success": True,
                "mensaje": f"Archivo {archivo.name} eliminado correctamente"
            }
            
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {str(e)}")
            return {
                "success": False,
                "error": f"Error eliminando archivo: {str(e)}"
            }
    
    def obtener_estadisticas_storage(self) -> Dict:
        """
        Obtiene estadísticas de uso de almacenamiento.
        
        Returns:
            Dict con estadísticas de storage
        """
        try:
            stats = {
                "input_dir": {
                    "archivos": len(list(self.input_dir.glob("*.pdf"))),
                    "tamaño_total": sum(f.stat().st_size for f in self.input_dir.glob("*.pdf"))
                },
                "output_dir": {
                    "archivos": len(list(self.output_dir.glob("*"))),
                    "tamaño_total": sum(f.stat().st_size for f in self.output_dir.glob("*") if f.is_file())
                },
                "logs_dir": {
                    "archivos": len(list(self.logs_dir.glob("*"))),
                    "tamaño_total": sum(f.stat().st_size for f in self.logs_dir.glob("*") if f.is_file())
                }
            }
            
            return stats
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {str(e)}")
            return {}