#!/usr/bin/env python3
"""
Script de instalación para el Sistema YaTeApruebo.
Instala dependencias y configura el entorno.
"""

import os
import sys
import subprocess
from pathlib import Path

def ejecutar_comando(comando, descripcion):
    """Ejecuta un comando y maneja errores."""
    print(f"🔧 {descripcion}...")
    try:
        result = subprocess.run(
            comando, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {descripcion} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {descripcion}: {e}")
        print(f"Salida del error: {e.stderr}")
        return False

def verificar_python():
    """Verifica que Python esté instalado y sea la versión correcta."""
    print("🐍 Verificando versión de Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Se requiere Python 3.8 o superior")
        print(f"Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def instalar_dependencias():
    """Instala las dependencias del proyecto."""
    print("📦 Instalando dependencias...")
    
    # Actualizar pip
    if not ejecutar_comando(
        f"{sys.executable} -m pip install --upgrade pip",
        "Actualizando pip"
    ):
        return False
    
    # Instalar requirements
    if not ejecutar_comando(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Instalando dependencias desde requirements.txt"
    ):
        return False
    
    return True

def crear_directorios():
    """Crea los directorios necesarios."""
    print("📁 Creando directorios necesarios...")
    
    directorios = [
        "data/input",
        "data/output", 
        "data/logs"
    ]
    
    for directorio in directorios:
        Path(directorio).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado: {directorio}")
    
    return True

def verificar_archivo_env():
    """Verifica que el archivo .env esté configurado."""
    print("🔐 Verificando configuración de variables de entorno...")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        if env_example_path.exists():
            print("⚠️ Archivo .env no encontrado, pero .env.example sí existe")
            print("📝 Por favor:")
            print("   1. Copia .env.example a .env")
            print("   2. Edita .env con tus tokens y API keys reales")
            return False
        else:
            print("❌ Ni .env ni .env.example encontrados")
            return False
    
    # Verificar que las variables críticas estén presentes
    try:
        with open(env_path, 'r') as f:
            contenido = f.read()
            
        variables_criticas = [
            "TELEGRAM_BOT_TOKEN",
            "OPENAI_API_KEY_AGENTE1", 
            "OPENAI_SEGUNDO_AGENTE"
        ]
        
        variables_faltantes = []
        for var in variables_criticas:
            if var not in contenido or f"{var}=your_" in contenido:
                variables_faltantes.append(var)
        
        if variables_faltantes:
            print("⚠️ Variables de entorno no configuradas:")
            for var in variables_faltantes:
                print(f"   • {var}")
            print("\n📝 Por favor configura estas variables en el archivo .env")
            return False
        
        print("✅ Archivo .env configurado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando .env: {e}")
        return False

def verificar_instalacion():
    """Verifica que la instalación sea correcta."""
    print("🔍 Verificando instalación...")
    
    try:
        # Intentar importar módulos principales
        from config.settings import settings
        from agents.secretaria_virtual import SecretariaVirtual
        from agents.analista_riesgos import AnalistaRiesgos
        
        print("✅ Todos los módulos se importaron correctamente")
        
        # Verificar configuración
        if settings.validate_config():
            print("✅ Configuración validada")
        else:
            print("⚠️ Algunas configuraciones pueden estar incompletas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

def mostrar_instrucciones_finales():
    """Muestra las instrucciones finales de uso."""
    print("\n" + "="*60)
    print("🎉 ¡INSTALACIÓN COMPLETADA!")
    print("="*60)
    print("\n📋 Para usar el sistema:")
    print("\n1. 🤖 Iniciar el bot de Telegram:")
    print("   python main.py")
    print("\n2. 🧪 Ejecutar pruebas:")
    print("   python test_system.py")
    print("\n3. 📊 Ver estadísticas:")
    print("   python -c \"from main import YaTeApruebaSystem; s = YaTeApruebaSystem(); print(s.obtener_estadisticas_sistema())\"")
    print("\n4. 📚 Documentación:")
    print("   Ver README.md para más detalles")
    print("\n" + "="*60)
    print("💡 Tip: Usa 'Ctrl+C' para detener el sistema")
    print("="*60)

def main():
    """Función principal de instalación."""
    print("🏦 INSTALADOR DEL SISTEMA YATEAPRUEBO")
    print("="*50)
    
    pasos = [
        ("Verificar Python", verificar_python),
        ("Crear directorios", crear_directorios),
        ("Instalar dependencias", instalar_dependencias),
        ("Verificar archivo .env", verificar_archivo_env),
        ("Verificar instalación", verificar_instalacion)
    ]
    
    errores = []
    
    for nombre_paso, funcion_paso in pasos:
        print(f"\n📋 Paso: {nombre_paso}")
        if not funcion_paso():
            errores.append(nombre_paso)
    
    print("\n" + "="*50)
    
    if errores:
        print("❌ INSTALACIÓN INCOMPLETA")
        print("\nPasos con errores:")
        for error in errores:
            print(f"   • {error}")
        print("\n💡 Revisa los errores anteriores y vuelve a ejecutar el instalador")
        return False
    else:
        mostrar_instrucciones_finales()
        return True

if __name__ == "__main__":
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado durante la instalación: {e}")
        sys.exit(1)