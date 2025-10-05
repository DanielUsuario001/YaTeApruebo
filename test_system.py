"""
Script de pruebas para el Sistema YaTeApruebo.
Permite probar el flujo completo sin usar Telegram.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from main import YaTeApruebaSystem
from loguru import logger

async def test_evaluacion_directa():
    """Prueba el sistema con datos de ejemplo."""
    logger.info("🧪 Iniciando prueba de evaluación directa")
    
    # Crear sistema
    sistema = YaTeApruebaSystem()
    
    # Datos de prueba
    nombre_empresa = "Empresa Ejemplo S.A."
    sector_empresa = "Manufacturero"
    
    # Nota: Necesitarías un archivo PDF real para esta prueba
    archivo_pdf = "data/input/ejemplo_estado_financiero.pdf"
    
    try:
        # Verificar si existe archivo de prueba
        if not Path(archivo_pdf).exists():
            logger.warning("⚠️ No se encontró archivo de prueba. Creando ejemplo...")
            
            # Crear directorio si no existe
            Path("data/input").mkdir(parents=True, exist_ok=True)
            
            # Crear archivo de texto de ejemplo (en lugar de PDF real)
            with open("data/input/ejemplo_datos.txt", "w", encoding="utf-8") as f:
                f.write("""
                ESTADO FINANCIERO DE PRUEBA
                ===========================
                
                Empresa: Empresa Ejemplo S.A.
                Sector: Manufacturero
                Periodo: 2023
                
                ACTIVOS:
                Activo Corriente: $1,500,000
                Efectivo: $300,000
                Cuentas por Cobrar: $800,000
                Inventarios: $400,000
                
                Activo No Corriente: $2,500,000
                Propiedad, Planta y Equipo: $2,500,000
                
                TOTAL ACTIVOS: $4,000,000
                
                PASIVOS:
                Pasivo Corriente: $800,000
                Cuentas por Pagar: $500,000
                Préstamos Corto Plazo: $300,000
                
                Pasivo No Corriente: $1,200,000
                Préstamos Largo Plazo: $1,200,000
                
                TOTAL PASIVOS: $2,000,000
                
                PATRIMONIO:
                Capital: $1,500,000
                Utilidades Retenidas: $500,000
                
                TOTAL PATRIMONIO: $2,000,000
                
                ESTADO DE RESULTADOS:
                Ingresos: $5,000,000
                Costo de Ventas: $3,000,000
                Utilidad Bruta: $2,000,000
                Gastos Operacionales: $1,500,000
                Utilidad Operacional: $500,000
                Gastos Financieros: $100,000
                Utilidad Neta: $400,000
                """)
            
            logger.info("📄 Archivo de ejemplo creado en data/input/ejemplo_datos.txt")
            logger.warning("⚠️ Para prueba completa, necesitas convertir este archivo a PDF")
            return
        
        # Ejecutar evaluación
        resultado = await sistema.procesar_evaluacion_directa(
            nombre_empresa=nombre_empresa,
            sector_empresa=sector_empresa,
            archivo_pdf=archivo_pdf
        )
        
        # Mostrar resultados
        if "error" in resultado:
            logger.error(f"❌ Error en evaluación: {resultado['error']}")
        else:
            logger.success("✅ Evaluación completada exitosamente!")
            logger.info(f"📊 Empresa: {resultado['empresa']}")
            logger.info(f"🎯 Calificación: {resultado['calificacion_riesgo']['nivel']}")
            logger.info(f"📄 Reporte generado: {resultado['pdf_path']}")
            
            # Mostrar resumen de calificación
            calificacion = resultado['calificacion_riesgo']
            logger.info("📋 Resumen de Calificación:")
            logger.info(f"   • Nivel: {calificacion['nivel']}")
            logger.info(f"   • Puntuación: {calificacion.get('puntuacion', 'N/A')}/100")
            logger.info(f"   • Justificación: {calificacion.get('justificacion', 'N/A')[:100]}...")
    
    except Exception as e:
        logger.error(f"❌ Error en prueba: {str(e)}")

async def test_inicializacion_servicios():
    """Prueba la inicialización de servicios."""
    logger.info("🧪 Probando inicialización de servicios")
    
    try:
        sistema = YaTeApruebaSystem()
        await sistema.inicializar_servicios()
        
        logger.success("✅ Servicios inicializados correctamente")
        
        # Probar estadísticas
        stats = sistema.obtener_estadisticas_sistema()
        logger.info("📊 Estadísticas del sistema:")
        logger.info(f"   • Versión: {stats['version']}")
        logger.info(f"   • Estado: {stats['estado']}")
        logger.info(f"   • Modelo OpenAI: {stats['configuracion']['modelo_openai']}")
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización: {str(e)}")

async def test_validaciones():
    """Prueba las validaciones del sistema."""
    logger.info("🧪 Probando validaciones")
    
    try:
        from utils.validators import DataValidator
        
        validator = DataValidator()
        
        # Probar validación de nombre de empresa
        nombres_test = [
            "Empresa Válida S.A.",
            "E",  # Muy corto
            "Empresa123@#$%",  # Caracteres inválidos
            "Empresa Normal Ltda."
        ]
        
        for nombre in nombres_test:
            resultado = validator.validar_nombre_empresa(nombre)
            status = "✅" if resultado else "❌"
            logger.info(f"   {status} '{nombre}': {resultado}")
        
        # Probar validación de sectores
        sectores_test = [
            "Manufacturero",
            "Servicios Financieros", 
            "X",  # Muy corto
            "Tecnología"
        ]
        
        for sector in sectores_test:
            resultado = validator.validar_sector_empresa(sector)
            status = "✅" if resultado else "❌"
            logger.info(f"   {status} '{sector}': {resultado}")
        
        logger.success("✅ Validaciones probadas")
        
    except Exception as e:
        logger.error(f"❌ Error en validaciones: {str(e)}")

def mostrar_menu():
    """Muestra el menú de opciones."""
    print("\n" + "="*60)
    print("🏦 SISTEMA YATEAPRUEBO - MODO PRUEBA")
    print("="*60)
    print("1. Probar inicialización de servicios")
    print("2. Probar validaciones")
    print("3. Probar evaluación directa (requiere PDF)")
    print("4. Ver estadísticas del sistema")
    print("5. Salir")
    print("="*60)

async def main_test():
    """Función principal de pruebas."""
    logger.info("🧪 Iniciando modo de pruebas")
    
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\nSelecciona una opción (1-5): ").strip()
            
            if opcion == "1":
                await test_inicializacion_servicios()
            elif opcion == "2":
                await test_validaciones()
            elif opcion == "3":
                await test_evaluacion_directa()
            elif opcion == "4":
                sistema = YaTeApruebaSystem()
                stats = sistema.obtener_estadisticas_sistema()
                print("\n📊 Estadísticas del Sistema:")
                print(f"   • Versión: {stats['version']}")
                print(f"   • Debug: {stats['configuracion']['debug']}")
                print(f"   • Modelo: {stats['configuracion']['modelo_openai']}")
            elif opcion == "5":
                logger.info("👋 Saliendo del modo de pruebas")
                break
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
                
        except KeyboardInterrupt:
            logger.info("\n⏹️ Pruebas interrumpidas por el usuario")
            break
        except Exception as e:
            logger.error(f"❌ Error en prueba: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main_test())
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        logger.error(f"❌ Error crítico: {str(e)}")