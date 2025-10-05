"""
Generador de reportes en PDF.
Crea documentos profesionales con los resultados del análisis.
"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue, red, green, orange
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

from config.settings import settings
from loguru import logger

class ReportGenerator:
    """
    Generador de reportes profesionales en PDF.
    
    Crea documentos estructurados con:
    - Portada profesional
    - Resumen ejecutivo
    - Análisis detallado
    - Tablas de indicadores
    - Recomendaciones
    - Anexos
    """
    
    def __init__(self):
        """Inicializa el generador de reportes."""
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.estilos = getSampleStyleSheet()
        
        # Crear estilos personalizados
        self._crear_estilos_personalizados()
        
        logger.info("📄 Generador de reportes inicializado")
    
    def _crear_estilos_personalizados(self):
        """Crea estilos personalizados para el reporte."""
        # Estilo para título principal
        self.estilos.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.estilos['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=blue,
            alignment=TA_CENTER
        ))
        
        # Estilo para subtítulos
        self.estilos.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.estilos['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=blue
        ))
        
        # Estilo para texto de calificación de riesgo
        self.estilos.add(ParagraphStyle(
            name='CalificacionRiesgo',
            parent=self.estilos['Normal'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            alignment=TA_CENTER,
            borderWidth=2,
            borderColor=blue
        ))
        
        # Estilo para recomendaciones
        self.estilos.add(ParagraphStyle(
            name='Recomendacion',
            parent=self.estilos['Normal'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=4,
            leftIndent=20
        ))
    
    async def generar_reporte_pdf(self, datos_analisis: Dict, session_id: str) -> str:
        """
        Genera el reporte completo en PDF.
        
        Args:
            datos_analisis: Datos del análisis financiero
            session_id: ID de la sesión
            
        Returns:
            Ruta del archivo PDF generado
        """
        try:
            # Generar nombre de archivo
            empresa_nombre = datos_analisis["empresa"]["nombre"].replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"Reporte_Financiero_{empresa_nombre}_{timestamp}.pdf"
            
            ruta_pdf = self.output_dir / nombre_archivo
            
            logger.info(f"📄 Generando reporte PDF: {nombre_archivo}")
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                str(ruta_pdf),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Construir contenido del documento
            contenido = []
            
            # 1. Portada
            contenido.extend(self._generar_portada(datos_analisis))
            contenido.append(PageBreak())
            
            # 2. Resumen ejecutivo
            contenido.extend(self._generar_resumen_ejecutivo(datos_analisis))
            contenido.append(PageBreak())
            
            # 3. Información de la empresa
            contenido.extend(self._generar_info_empresa(datos_analisis))
            
            # 4. Calificación de riesgo
            contenido.extend(self._generar_calificacion_riesgo(datos_analisis))
            
            # 5. Análisis detallado
            contenido.extend(self._generar_analisis_detallado(datos_analisis))
            contenido.append(PageBreak())
            
            # 6. Recomendaciones
            contenido.extend(self._generar_recomendaciones(datos_analisis))
            
            # 7. Perfil de aprobador
            contenido.extend(self._generar_perfil_aprobador(datos_analisis))
            
            # 8. Anexos
            contenido.extend(self._generar_anexos(datos_analisis))
            
            # Construir PDF
            doc.build(contenido)
            
            logger.info(f"✅ Reporte PDF generado: {nombre_archivo}")
            
            return str(ruta_pdf)
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte PDF: {str(e)}")
            raise Exception(f"Error generando reporte: {str(e)}")
    
    def _generar_portada(self, datos: Dict) -> List:
        """Genera la portada del reporte."""
        contenido = []
        
        # Título principal
        contenido.append(Spacer(1, 2*inch))
        contenido.append(Paragraph(
            "REPORTE DE ANÁLISIS FINANCIERO",
            self.estilos['TituloPrincipal']
        ))
        
        contenido.append(Spacer(1, 0.5*inch))
        
        # Información de la empresa
        empresa_info = f"""
        <b>EMPRESA EVALUADA:</b><br/>
        {datos['empresa']['nombre']}<br/>
        <b>SECTOR:</b> {datos['empresa']['sector']}<br/>
        <b>FECHA DE ANÁLISIS:</b> {datetime.now().strftime('%d de %B de %Y')}
        """
        
        contenido.append(Paragraph(empresa_info, self.estilos['Normal']))
        
        contenido.append(Spacer(1, 1*inch))
        
        # Logo/branding del sistema
        contenido.append(Paragraph(
            "<b>SISTEMA YATEAPRUEBO</b><br/>Evaluación Inteligente de Estados Financieros",
            self.estilos['Normal']
        ))
        
        contenido.append(Spacer(1, 1*inch))
        
        # Calificación de riesgo destacada
        calificacion = datos["calificacion_riesgo"]["nivel"]
        color_riesgo = self._obtener_color_riesgo(calificacion)
        
        calificacion_texto = f"""
        <b>CALIFICACIÓN DE RIESGO:</b><br/>
        <font color="{color_riesgo}"><b>{calificacion}</b></font>
        """
        
        contenido.append(Paragraph(calificacion_texto, self.estilos['CalificacionRiesgo']))
        
        return contenido
    
    def _generar_resumen_ejecutivo(self, datos: Dict) -> List:
        """Genera el resumen ejecutivo."""
        contenido = []
        
        contenido.append(Paragraph("RESUMEN EJECUTIVO", self.estilos['TituloPrincipal']))
        contenido.append(Spacer(1, 20))
        
        # Resumen del análisis
        resumen_texto = datos.get("resumen_ejecutivo", "Resumen ejecutivo no disponible.")
        contenido.append(Paragraph(resumen_texto, self.estilos['Normal']))
        
        contenido.append(Spacer(1, 20))
        
        # Tabla de indicadores clave
        tabla_indicadores = self._crear_tabla_indicadores_clave(datos)
        if tabla_indicadores:
            contenido.append(Paragraph("INDICADORES CLAVE", self.estilos['Subtitulo']))
            contenido.append(tabla_indicadores)
        
        return contenido
    
    def _generar_info_empresa(self, datos: Dict) -> List:
        """Genera la sección de información de la empresa."""
        contenido = []
        
        contenido.append(Paragraph("INFORMACIÓN DE LA EMPRESA", self.estilos['Subtitulo']))
        
        empresa = datos["empresa"]
        
        info_empresa = [
            ["Campo", "Valor"],
            ["Nombre de la Empresa", empresa["nombre"]],
            ["Sector", empresa["sector"]],
            ["Fecha de Análisis", datos["fecha_analisis"][:10]],
        ]
        
        tabla = Table(info_empresa, colWidths=[2*inch, 4*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))
        
        contenido.append(tabla)
        contenido.append(Spacer(1, 20))
        
        return contenido
    
    def _generar_calificacion_riesgo(self, datos: Dict) -> List:
        """Genera la sección de calificación de riesgo."""
        contenido = []
        
        contenido.append(Paragraph("CALIFICACIÓN DE RIESGO", self.estilos['Subtitulo']))
        
        calificacion = datos["calificacion_riesgo"]
        
        # Tabla de calificación
        datos_calificacion = [
            ["Aspecto", "Resultado"],
            ["Nivel de Riesgo", calificacion["nivel"]],
            ["Puntuación", f"{calificacion.get('puntuacion', 'N/A')}/100"],
            ["Justificación", calificacion.get("justificacion", "No disponible")[:200] + "..."]
        ]
        
        tabla = Table(datos_calificacion, colWidths=[2*inch, 4*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        contenido.append(tabla)
        contenido.append(Spacer(1, 20))
        
        return contenido
    
    def _generar_analisis_detallado(self, datos: Dict) -> List:
        """Genera el análisis detallado por categorías."""
        contenido = []
        
        contenido.append(Paragraph("ANÁLISIS DETALLADO", self.estilos['TituloPrincipal']))
        
        analisis_detallado = datos.get("analisis_detallado", {})
        
        categorias = ["liquidez", "solvencia", "rentabilidad", "eficiencia", "sectorial"]
        
        for categoria in categorias:
            if categoria in analisis_detallado:
                contenido.extend(self._generar_seccion_categoria(categoria, analisis_detallado[categoria]))
        
        return contenido
    
    def _generar_seccion_categoria(self, categoria: str, datos_categoria: Dict) -> List:
        """Genera una sección de análisis por categoría."""
        contenido = []
        
        titulo_categoria = categoria.upper().replace("_", " ")
        contenido.append(Paragraph(f"ANÁLISIS DE {titulo_categoria}", self.estilos['Subtitulo']))
        
        if "error" in datos_categoria:
            contenido.append(Paragraph(
                f"Error en análisis de {categoria}: {datos_categoria['error']}",
                self.estilos['Normal']
            ))
        else:
            resultado = datos_categoria.get("resultado", {})
            
            # Agregar descripción si está disponible
            if isinstance(resultado, dict):
                for key, value in resultado.items():
                    if isinstance(value, str) and len(value) > 20:
                        contenido.append(Paragraph(f"<b>{key.title()}:</b> {value}", self.estilos['Normal']))
                    elif isinstance(value, (int, float)):
                        contenido.append(Paragraph(f"<b>{key.title()}:</b> {value}", self.estilos['Normal']))
            else:
                contenido.append(Paragraph(str(resultado), self.estilos['Normal']))
        
        contenido.append(Spacer(1, 15))
        
        return contenido
    
    def _generar_recomendaciones(self, datos: Dict) -> List:
        """Genera la sección de recomendaciones."""
        contenido = []
        
        contenido.append(Paragraph("RECOMENDACIONES", self.estilos['Subtitulo']))
        
        recomendaciones = datos.get("recomendaciones", [])
        
        if not recomendaciones:
            contenido.append(Paragraph("No hay recomendaciones específicas disponibles.", self.estilos['Normal']))
        else:
            for i, recomendacion in enumerate(recomendaciones[:10], 1):  # Limitar a 10
                contenido.append(Paragraph(
                    f"{i}. {recomendacion}",
                    self.estilos['Recomendacion']
                ))
        
        contenido.append(Spacer(1, 20))
        
        return contenido
    
    def _generar_perfil_aprobador(self, datos: Dict) -> List:
        """Genera la sección del perfil de aprobador recomendado."""
        contenido = []
        
        contenido.append(Paragraph("PERFIL DE APROBADOR RECOMENDADO", self.estilos['Subtitulo']))
        
        perfil = datos.get("perfil_aprobador", {})
        
        if not perfil:
            contenido.append(Paragraph("Información de perfil no disponible.", self.estilos['Normal']))
        else:
            datos_perfil = [
                ["Aspecto", "Requerimiento"],
                ["Perfil Profesional", perfil.get("perfil", "No especificado")],
                ["Experiencia Mínima", perfil.get("experiencia_minima", "No especificada")],
                ["Especialidad", perfil.get("especialidad", "No especificada")],
                ["Autoridad de Aprobación", perfil.get("autoridad", "No especificada")],
                ["Supervisión Requerida", perfil.get("supervision", "No especificada")]
            ]
            
            tabla = Table(datos_perfil, colWidths=[2.5*inch, 3.5*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            contenido.append(tabla)
        
        contenido.append(Spacer(1, 20))
        
        return contenido
    
    def _generar_anexos(self, datos: Dict) -> List:
        """Genera los anexos del reporte."""
        contenido = []
        
        contenido.append(Paragraph("ANEXOS", self.estilos['Subtitulo']))
        
        # Anexo 1: Metodología
        contenido.append(Paragraph("Anexo 1: Metodología de Análisis", self.estilos['Heading3']))
        metodologia = """
        Este análisis ha sido realizado utilizando inteligencia artificial especializada en análisis financiero.
        La evaluación incluye análisis de liquidez, solvencia, rentabilidad, eficiencia operativa y riesgos sectoriales.
        
        Los indicadores han sido calculados basándose en las mejores prácticas de análisis financiero y 
        comparados con estándares de la industria correspondiente.
        """
        contenido.append(Paragraph(metodologia, self.estilos['Normal']))
        
        contenido.append(Spacer(1, 15))
        
        # Anexo 2: Criterios de calificación
        contenido.append(Paragraph("Anexo 2: Criterios de Calificación de Riesgo", self.estilos['Heading3']))
        
        criterios_tabla = [
            ["Nivel", "Descripción", "Acción Recomendada"],
            ["BÁSICO", "Riesgo bajo, empresa sólida", "Aprobación automática o revisión mínima"],
            ["INTERMEDIO", "Riesgo moderado", "Análisis humano adicional requerido"],
            ["AVANZADO", "Riesgo alto", "Análisis exhaustivo por especialista senior"]
        ]
        
        tabla_criterios = Table(criterios_tabla, colWidths=[1.5*inch, 2.5*inch, 2*inch])
        tabla_criterios.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        contenido.append(tabla_criterios)
        
        # Información del sistema
        contenido.append(Spacer(1, 20))
        contenido.append(Paragraph("Anexo 3: Información del Sistema", self.estilos['Heading3']))
        
        info_sistema = f"""
        Sistema: YaTeApruebo v{settings.VERSION}
        Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        Modelo de IA utilizado: {settings.OPENAI_MODEL}
        
        Este reporte ha sido generado automáticamente por el sistema YaTeApruebo.
        Para consultas o aclaraciones, contacte al administrador del sistema.
        """
        
        contenido.append(Paragraph(info_sistema, self.estilos['Normal']))
        
        return contenido
    
    def _crear_tabla_indicadores_clave(self, datos: Dict) -> Optional[Table]:
        """Crea una tabla con los indicadores clave del análisis."""
        try:
            calificacion = datos["calificacion_riesgo"]
            
            datos_tabla = [
                ["Indicador", "Valor"],
                ["Calificación Global", calificacion["nivel"]],
                ["Puntuación", f"{calificacion.get('puntuacion', 'N/A')}/100"],
            ]
            
            # Agregar algunos indicadores del análisis detallado si están disponibles
            analisis = datos.get("analisis_detallado", {})
            
            for categoria in ["liquidez", "solvencia", "rentabilidad"]:
                if categoria in analisis and "resultado" in analisis[categoria]:
                    resultado = analisis[categoria]["resultado"]
                    if isinstance(resultado, dict):
                        # Tomar el primer indicador numérico encontrado
                        for key, value in resultado.items():
                            if isinstance(value, (int, float)):
                                datos_tabla.append([f"{categoria.title()} - {key}", str(value)])
                                break
            
            tabla = Table(datos_tabla, colWidths=[3*inch, 2*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
                ('GRID', (0, 0), (-1, -1), 1, black),
            ]))
            
            return tabla
            
        except Exception as e:
            logger.error(f"❌ Error creando tabla de indicadores: {str(e)}")
            return None
    
    def _obtener_color_riesgo(self, nivel_riesgo: str) -> str:
        """Obtiene el color asociado al nivel de riesgo."""
        colores = {
            "BASICO": "green",
            "INTERMEDIO": "orange", 
            "AVANZADO": "red"
        }
        return colores.get(nivel_riesgo, "black")
    
    async def generar_reporte_texto(self, datos_analisis: Dict, session_id: str) -> str:
        """
        Genera un reporte en formato texto plano.
        
        Args:
            datos_analisis: Datos del análisis
            session_id: ID de la sesión
            
        Returns:
            Ruta del archivo de texto generado
        """
        try:
            empresa_nombre = datos_analisis["empresa"]["nombre"].replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"Reporte_Texto_{empresa_nombre}_{timestamp}.txt"
            
            ruta_txt = self.output_dir / nombre_archivo
            
            contenido_texto = self._generar_contenido_texto(datos_analisis)
            
            with open(ruta_txt, 'w', encoding='utf-8') as f:
                f.write(contenido_texto)
            
            logger.info(f"📄 Reporte de texto generado: {nombre_archivo}")
            
            return str(ruta_txt)
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte de texto: {str(e)}")
            raise Exception(f"Error generando reporte de texto: {str(e)}")
    
    def _generar_contenido_texto(self, datos: Dict) -> str:
        """Genera el contenido del reporte en formato texto."""
        lineas = []
        
        lineas.append("=" * 80)
        lineas.append("REPORTE DE ANÁLISIS FINANCIERO - SISTEMA YATEAPRUEBO")
        lineas.append("=" * 80)
        lineas.append("")
        
        # Información básica
        lineas.append(f"EMPRESA: {datos['empresa']['nombre']}")
        lineas.append(f"SECTOR: {datos['empresa']['sector']}")
        lineas.append(f"FECHA DE ANÁLISIS: {datos['fecha_analisis'][:10]}")
        lineas.append("")
        
        # Calificación de riesgo
        calificacion = datos["calificacion_riesgo"]
        lineas.append("CALIFICACIÓN DE RIESGO")
        lineas.append("-" * 30)
        lineas.append(f"Nivel: {calificacion['nivel']}")
        lineas.append(f"Puntuación: {calificacion.get('puntuacion', 'N/A')}/100")
        lineas.append(f"Justificación: {calificacion.get('justificacion', 'No disponible')}")
        lineas.append("")
        
        # Resumen ejecutivo
        lineas.append("RESUMEN EJECUTIVO")
        lineas.append("-" * 30)
        lineas.append(datos.get('resumen_ejecutivo', 'No disponible'))
        lineas.append("")
        
        # Recomendaciones
        lineas.append("RECOMENDACIONES")
        lineas.append("-" * 30)
        recomendaciones = datos.get("recomendaciones", [])
        for i, rec in enumerate(recomendaciones, 1):
            lineas.append(f"{i}. {rec}")
        lineas.append("")
        
        # Perfil de aprobador
        perfil = datos.get("perfil_aprobador", {})
        lineas.append("PERFIL DE APROBADOR RECOMENDADO")
        lineas.append("-" * 30)
        lineas.append(f"Perfil: {perfil.get('perfil', 'No especificado')}")
        lineas.append(f"Experiencia: {perfil.get('experiencia_minima', 'No especificada')}")
        lineas.append(f"Especialidad: {perfil.get('especialidad', 'No especificada')}")
        lineas.append("")
        
        lineas.append("=" * 80)
        lineas.append(f"Generado por Sistema YaTeApruebo - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lineas.append("=" * 80)
        
        return "\n".join(lineas)