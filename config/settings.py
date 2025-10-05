"""
Configuración centralizada del sistema YaTeApruebo.
Maneja variables de entorno y configuraciones globales.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List

# Cargar variables de entorno
load_dotenv()

class Settings:
    """Configuraciones del sistema YaTeApruebo."""
    
    # Información del proyecto
    PROJECT_NAME: str = "YaTeApruebo"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema de evaluación inteligente de estados financieros"
    
    # Configuración de Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Configuración de OpenAI
    OPENAI_API_KEY_AGENTE1: str = os.getenv("OPENAI_API_KEY_AGENTE1", "")
    OPENAI_SEGUNDO_AGENTE: str = os.getenv("OPENAI_SEGUNDO_AGENTE", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    
    # Configuración de directorios
    BASE_DIR: Path = Path(__file__).parent.parent
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "./data")
    INPUT_DIR: str = os.getenv("INPUT_DIR", "./data/input")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./data/output")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "./data/logs")
    
    # Configuración de archivos
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_FILE_TYPES: List[str] = os.getenv("ALLOWED_FILE_TYPES", "pdf").split(",")
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Configuración de análisis de riesgo
    RISK_LEVELS: List[str] = os.getenv("RISK_LEVELS", "BASICO,INTERMEDIO,AVANZADO").split(",")
    DEFAULT_RISK_LEVEL: str = os.getenv("DEFAULT_RISK_LEVEL", "INTERMEDIO")
    
    # Configuración futura de Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valida que las configuraciones críticas estén presentes."""
        required_vars = [
            cls.TELEGRAM_BOT_TOKEN,
            cls.OPENAI_API_KEY_AGENTE1,
            cls.OPENAI_SEGUNDO_AGENTE
        ]
        
        missing_vars = [var for var in required_vars if not var]
        
        if missing_vars:
            print(f"❌ Faltan variables de entorno críticas: {len(missing_vars)} variables")
            return False
        
        print("✅ Configuración validada correctamente")
        return True
    
    @classmethod
    def create_directories(cls) -> None:
        """Crea los directorios necesarios si no existen."""
        directories = [
            cls.INPUT_DIR,
            cls.OUTPUT_DIR,
            cls.LOGS_DIR
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        print("✅ Directorios creados/verificados correctamente")

# Instancia global de configuración
settings = Settings()

# Validar configuración al importar
if __name__ == "__main__":
    settings.validate_config()
    settings.create_directories()