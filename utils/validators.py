"""
Validadores para el sistema YaTeApruebo.
Contiene funciones para validar datos de entrada.
"""

import re
from typing import Dict, List, Optional
from pathlib import Path

from config.settings import settings
from loguru import logger

class DataValidator:
    """
    Clase para validar datos de entrada en el sistema.
    
    Valida información de empresas, archivos, y otros datos críticos.
    """
    
    def __init__(self):
        """Inicializa el validador."""
        # Sectores empresariales válidos
        self.sectores_validos = [
            "Agricultura", "Ganadería", "Pesca", "Minería", "Petróleo",
            "Manufacturero", "Textil", "Alimentos", "Bebidas", "Automotriz",
            "Construcción", "Inmobiliario", "Comercio", "Retail", "Mayorista",
            "Transporte", "Logística", "Telecomunicaciones", "Servicios",
            "Financiero", "Bancario", "Seguros", "Tecnología", "Software",
            "Turismo", "Hotelería", "Restaurantes", "Educación", "Salud",
            "Farmacéutico", "Energía", "Utilities", "Medios", "Entretenimiento",
            "Consultoría", "Legal", "Otros"
        ]
        
        logger.info("✅ Validador de datos inicializado")
    
    def validar_nombre_empresa(self, nombre: str) -> bool:
        """
        Valida que el nombre de empresa sea válido.
        
        Args:
            nombre: Nombre de la empresa a validar
            
        Returns:
            True si es válido, False en caso contrario
        """
        if not nombre or not isinstance(nombre, str):
            logger.warning("❌ Nombre de empresa vacío o no es string")
            return False
        
        nombre = nombre.strip()
        
        # Longitud mínima y máxima
        if len(nombre) < 3:
            logger.warning("❌ Nombre de empresa muy corto")
            return False
        
        if len(nombre) > 200:
            logger.warning("❌ Nombre de empresa muy largo")
            return False
        
        # Caracteres válidos (letras, números, espacios, algunos símbolos)
        patron_valido = re.compile(r'^[a-zA-ZáéíóúñÑ0-9\s\.\-_&(),"\']+$')
        if not patron_valido.match(nombre):
            logger.warning(f"❌ Nombre de empresa contiene caracteres inválidos: {nombre}")
            return False
        
        # No puede ser solo números o espacios
        if nombre.replace(" ", "").isdigit():
            logger.warning("❌ Nombre de empresa no puede ser solo números")
            return False
        
        logger.debug(f"✅ Nombre de empresa válido: {nombre}")
        return True
    
    def validar_sector_empresa(self, sector: str) -> bool:
        """
        Valida que el sector de empresa sea válido.
        
        Args:
            sector: Sector de la empresa a validar
            
        Returns:
            True si es válido, False en caso contrario
        """
        if not sector or not isinstance(sector, str):
            logger.warning("❌ Sector de empresa vacío o no es string")
            return False
        
        sector = sector.strip().title()  # Capitalizar primera letra
        
        # Longitud mínima
        if len(sector) < 3:
            logger.warning("❌ Sector de empresa muy corto")
            return False
        
        if len(sector) > 100:
            logger.warning("❌ Sector de empresa muy largo") 
            return False
        
        # Verificar si está en la lista de sectores válidos (flexible)
        sector_encontrado = False
        for sector_valido in self.sectores_validos:
            if (sector.lower() in sector_valido.lower() or 
                sector_valido.lower() in sector.lower()):
                sector_encontrado = True
                break
        
        if not sector_encontrado:
            logger.info(f"⚠️ Sector no reconocido, pero se acepta: {sector}")
        
        # Caracteres válidos
        patron_valido = re.compile(r'^[a-zA-ZáéíóúñÑ\s\-_&]+$')
        if not patron_valido.match(sector):
            logger.warning(f"❌ Sector contiene caracteres inválidos: {sector}")
            return False
        
        logger.debug(f"✅ Sector de empresa válido: {sector}")
        return True
    
    def validar_archivo_pdf(self, archivo_path: str) -> Dict:
        """
        Valida que un archivo PDF sea válido para procesamiento.
        
        Args:
            archivo_path: Ruta del archivo a validar
            
        Returns:
            Dict con resultado de la validación
        """
        try:
            archivo = Path(archivo_path)
            
            # Verificar existencia
            if not archivo.exists():
                return {
                    "valido": False,
                    "error": "Archivo no encontrado",
                    "codigo_error": "FILE_NOT_FOUND"
                }
            
            # Verificar extensión
            if archivo.suffix.lower() != '.pdf':
                return {
                    "valido": False,
                    "error": "El archivo debe ser un PDF",
                    "codigo_error": "INVALID_EXTENSION"
                }
            
            # Verificar tamaño
            tamaño = archivo.stat().st_size
            if tamaño == 0:
                return {
                    "valido": False,
                    "error": "Archivo vacío",
                    "codigo_error": "EMPTY_FILE"
                }
            
            if tamaño > settings.MAX_FILE_SIZE:
                tamaño_mb = tamaño / (1024 * 1024)
                limite_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                return {
                    "valido": False,
                    "error": f"Archivo muy grande ({tamaño_mb:.1f}MB). Límite: {limite_mb:.1f}MB",
                    "codigo_error": "FILE_TOO_LARGE"
                }
            
            # Verificar nombre de archivo
            if not self._validar_nombre_archivo(archivo.name):
                return {
                    "valido": False,
                    "error": "Nombre de archivo inválido",
                    "codigo_error": "INVALID_FILENAME"
                }
            
            logger.debug(f"✅ Archivo PDF válido: {archivo.name}")
            return {
                "valido": True,
                "tamaño": tamaño,
                "nombre": archivo.name
            }
            
        except Exception as e:
            logger.error(f"❌ Error validando archivo PDF: {str(e)}")
            return {
                "valido": False,
                "error": f"Error validando archivo: {str(e)}",
                "codigo_error": "VALIDATION_ERROR"
            }
    
    def _validar_nombre_archivo(self, nombre_archivo: str) -> bool:
        """Valida que el nombre del archivo sea seguro."""
        # Caracteres no permitidos en nombres de archivo
        caracteres_prohibidos = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        
        for char in caracteres_prohibidos:
            if char in nombre_archivo:
                return False
        
        # Longitud máxima
        if len(nombre_archivo) > 255:
            return False
        
        # No puede empezar con punto
        if nombre_archivo.startswith('.'):
            return False
        
        return True
    
    def validar_session_id(self, session_id: str) -> bool:
        """
        Valida que un session_id sea válido.
        
        Args:
            session_id: ID de sesión a validar
            
        Returns:
            True si es válido, False en caso contrario
        """
        if not session_id or not isinstance(session_id, str):
            return False
        
        # Patrón esperado: session_userid_timestamp
        patron = re.compile(r'^session_\d+_\d{8}_\d{6}$')
        
        if not patron.match(session_id):
            logger.warning(f"❌ Session ID inválido: {session_id}")
            return False
        
        return True
    
    def validar_calificacion_riesgo(self, calificacion: str) -> bool:
        """
        Valida que una calificación de riesgo sea válida.
        
        Args:
            calificacion: Calificación a validar
            
        Returns:
            True si es válida, False en caso contrario
        """
        if not calificacion or not isinstance(calificacion, str):
            return False
        
        calificacion = calificacion.upper().strip()
        
        return calificacion in settings.RISK_LEVELS
    
    def validar_datos_empresa_completos(self, datos_empresa: Dict) -> Dict:
        """
        Valida que los datos de empresa estén completos.
        
        Args:
            datos_empresa: Diccionario con datos de empresa
            
        Returns:
            Dict con resultado de la validación
        """
        errores = []
        
        # Verificar campos requeridos
        campos_requeridos = ['nombre', 'sector']
        
        for campo in campos_requeridos:
            if campo not in datos_empresa:
                errores.append(f"Campo requerido faltante: {campo}")
            elif not datos_empresa[campo]:
                errores.append(f"Campo vacío: {campo}")
        
        # Validar nombre si existe
        if 'nombre' in datos_empresa and datos_empresa['nombre']:
            if not self.validar_nombre_empresa(datos_empresa['nombre']):
                errores.append("Nombre de empresa inválido")
        
        # Validar sector si existe
        if 'sector' in datos_empresa and datos_empresa['sector']:
            if not self.validar_sector_empresa(datos_empresa['sector']):
                errores.append("Sector de empresa inválido")
        
        if errores:
            return {
                "valido": False,
                "errores": errores
            }
        
        return {
            "valido": True,
            "datos": datos_empresa
        }
    
    def sanitizar_texto(self, texto: str, max_length: Optional[int] = None) -> str:
        """
        Sanitiza texto eliminando caracteres problemáticos.
        
        Args:
            texto: Texto a sanitizar
            max_length: Longitud máxima (opcional)
            
        Returns:
            Texto sanitizado
        """
        if not texto or not isinstance(texto, str):
            return ""
        
        # Eliminar caracteres de control
        texto_limpio = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)
        
        # Normalizar espacios
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        
        # Trim
        texto_limpio = texto_limpio.strip()
        
        # Limitar longitud si se especifica
        if max_length and len(texto_limpio) > max_length:
            texto_limpio = texto_limpio[:max_length].strip()
        
        return texto_limpio
    
    def obtener_sectores_disponibles(self) -> List[str]:
        """
        Obtiene la lista de sectores empresariales disponibles.
        
        Returns:
            Lista de sectores válidos
        """
        return self.sectores_validos.copy()
    
    def sugerir_sector(self, sector_input: str) -> Optional[str]:
        """
        Sugiere un sector válido basado en el input del usuario.
        
        Args:
            sector_input: Input del usuario
            
        Returns:
            Sector sugerido o None si no hay coincidencia
        """
        if not sector_input:
            return None
        
        sector_input = sector_input.lower().strip()
        
        # Buscar coincidencia exacta
        for sector in self.sectores_validos:
            if sector.lower() == sector_input:
                return sector
        
        # Buscar coincidencia parcial
        for sector in self.sectores_validos:
            if sector_input in sector.lower() or sector.lower() in sector_input:
                return sector
        
        return None