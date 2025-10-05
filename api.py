"""
API REST para el Sistema YaTeApruebo.
Proporciona endpoints HTTP para integraciones externas.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn
from typing import Optional
import json
from pathlib import Path
import tempfile
import os

from main import YaTeApruebaSystem
from config.settings import settings

# Crear aplicación FastAPI
app = FastAPI(
    title="YaTeApruebo API",
    description="API REST para evaluación inteligente de estados financieros",
    version=settings.VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global del sistema
sistema_global: Optional[YaTeApruebaSystem] = None

@app.on_event("startup")
async def startup_event():
    """Inicializa el sistema al arrancar la API."""
    global sistema_global
    sistema_global = YaTeApruebaSystem()
    await sistema_global.inicializar_servicios()

@app.get("/")
async def root():
    """Endpoint raíz de bienvenida."""
    return {
        "mensaje": "🏦 Bienvenido a YaTeApruebo API",
        "version": settings.VERSION,
        "descripcion": settings.DESCRIPTION,
        "documentacion": "/docs"
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del sistema."""
    try:
        stats = sistema_global.obtener_estadisticas_sistema() if sistema_global else {}
        return {
            "status": "healthy",
            "sistema_iniciado": sistema_global is not None,
            "estadisticas": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en health check: {str(e)}")

@app.post("/evaluacion")
async def crear_evaluacion(
    nombre_empresa: str = Form(...),
    sector_empresa: str = Form(...),
    archivo_pdf: UploadFile = File(...)
):
    """
    Crea una nueva evaluación financiera.
    
    Args:
        nombre_empresa: Nombre de la empresa a evaluar
        sector_empresa: Sector de la empresa
        archivo_pdf: Archivo PDF con el estado financiero
        
    Returns:
        Resultado de la evaluación completa
    """
    if not sistema_global:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")
    
    # Validar archivo PDF
    if not archivo_pdf.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    
    if archivo_pdf.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Archivo muy grande")
    
    try:
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await archivo_pdf.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Procesar evaluación
            resultado = await sistema_global.procesar_evaluacion_directa(
                nombre_empresa=nombre_empresa,
                sector_empresa=sector_empresa,
                archivo_pdf=temp_file_path
            )
            
            if "error" in resultado:
                raise HTTPException(status_code=400, detail=resultado["error"])
            
            # Remover datos muy grandes de la respuesta
            resultado_limpio = {
                "success": resultado["success"],
                "session_id": resultado["session_id"],
                "empresa": resultado["empresa"],
                "calificacion_riesgo": resultado["calificacion_riesgo"],
                "pdf_path": resultado["pdf_path"],
                "resumen": resultado["reporte_completo"].get("resumen_ejecutivo", "No disponible")
            }
            
            return resultado_limpio
            
        finally:
            # Limpiar archivo temporal
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando evaluación: {str(e)}")

@app.get("/evaluacion/{session_id}/reporte")
async def descargar_reporte(session_id: str):
    """
    Descarga el reporte PDF de una evaluación.
    
    Args:
        session_id: ID de la sesión de evaluación
        
    Returns:
        Archivo PDF del reporte
    """
    try:
        # Buscar archivo de reporte
        output_dir = Path(settings.OUTPUT_DIR)
        archivos_reporte = list(output_dir.glob(f"Reporte_Financiero_*{session_id}*.pdf"))
        
        if not archivos_reporte:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
        
        archivo_reporte = archivos_reporte[0]  # Tomar el más reciente
        
        if not archivo_reporte.exists():
            raise HTTPException(status_code=404, detail="Archivo de reporte no encontrado")
        
        return FileResponse(
            archivo_reporte,
            media_type='application/pdf',
            filename=archivo_reporte.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descargando reporte: {str(e)}")

@app.get("/evaluacion/{session_id}/detalle")
async def obtener_detalle_evaluacion(session_id: str):
    """
    Obtiene los detalles completos de una evaluación.
    
    Args:
        session_id: ID de la sesión
        
    Returns:
        Detalles completos de la evaluación
    """
    try:
        # Buscar archivo de análisis completo
        output_dir = Path(settings.OUTPUT_DIR)
        archivo_analisis = output_dir / f"{session_id}_analisis_completo.json"
        
        if not archivo_analisis.exists():
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        
        with open(archivo_analisis, 'r', encoding='utf-8') as f:
            analisis_completo = json.load(f)
        
        return analisis_completo
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo detalles: {str(e)}")

@app.get("/estadisticas")
async def obtener_estadisticas():
    """Obtiene estadísticas del sistema."""
    if not sistema_global:
        raise HTTPException(status_code=503, detail="Sistema no inicializado")
    
    try:
        return sistema_global.obtener_estadisticas_sistema()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.get("/evaluaciones")
async def listar_evaluaciones():
    """Lista todas las evaluaciones realizadas."""
    try:
        output_dir = Path(settings.OUTPUT_DIR)
        archivos_analisis = list(output_dir.glob("*_analisis_completo.json"))
        
        evaluaciones = []
        
        for archivo in archivos_analisis:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    analisis = json.load(f)
                
                evaluaciones.append({
                    "session_id": analisis.get("session_id"),
                    "empresa": analisis.get("empresa", {}).get("nombre"),
                    "sector": analisis.get("empresa", {}).get("sector"),
                    "fecha_analisis": analisis.get("fecha_analisis"),
                    "calificacion_riesgo": analisis.get("calificacion_riesgo", {}).get("nivel"),
                    "puntuacion": analisis.get("calificacion_riesgo", {}).get("puntuacion")
                })
                
            except Exception:
                continue  # Saltar archivos corruptos
        
        # Ordenar por fecha más reciente
        evaluaciones.sort(key=lambda x: x["fecha_analisis"] or "", reverse=True)
        
        return {
            "total": len(evaluaciones),
            "evaluaciones": evaluaciones
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando evaluaciones: {str(e)}")

@app.delete("/evaluacion/{session_id}")
async def eliminar_evaluacion(session_id: str):
    """
    Elimina una evaluación y sus archivos asociados.
    
    Args:
        session_id: ID de la sesión a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    try:
        output_dir = Path(settings.OUTPUT_DIR)
        input_dir = Path(settings.INPUT_DIR)
        
        archivos_eliminados = []
        
        # Buscar y eliminar archivos relacionados
        patrones = [
            f"{session_id}*.json",
            f"*{session_id}*.pdf",
            f"*{session_id}*.txt"
        ]
        
        for patron in patrones:
            # Buscar en output
            for archivo in output_dir.glob(patron):
                archivo.unlink()
                archivos_eliminados.append(str(archivo))
            
            # Buscar en input
            for archivo in input_dir.glob(patron):
                archivo.unlink()
                archivos_eliminados.append(str(archivo))
        
        if not archivos_eliminados:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        
        return {
            "mensaje": "Evaluación eliminada exitosamente",
            "archivos_eliminados": archivos_eliminados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando evaluación: {str(e)}")

def iniciar_api_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Inicia el servidor de la API.
    
    Args:
        host: Host donde ejecutar el servidor
        port: Puerto donde ejecutar el servidor
    """
    print(f"🚀 Iniciando API YaTeApruebo en http://{host}:{port}")
    print(f"📚 Documentación disponible en http://{host}:{port}/docs")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    iniciar_api_server()