@echo off
echo.
echo ============================================================
echo 🏦 SISTEMA YATEAPRUEBO - INICIO RAPIDO
echo ============================================================
echo.
echo Selecciona una opcion:
echo.
echo 1. Ejecutar solo Telegram Bot
echo 2. Ejecutar solo API REST
echo 3. Modo de pruebas
echo 4. Ver documentacion de API
echo 5. Instalar/Actualizar dependencias
echo 6. Salir
echo.
set /p option="Opcion (1-6): "

if "%option%"=="1" goto telegram
if "%option%"=="2" goto api
if "%option%"=="3" goto test
if "%option%"=="4" goto docs
if "%option%"=="5" goto install
if "%option%"=="6" goto exit

:telegram
echo.
echo 📱 Iniciando Bot de Telegram...
echo ⏹️ Presiona Ctrl+C para detener
echo.
C:/Users/fifa2/AppData/Local/Programs/Python/Python313/python.exe main.py
goto end

:api
echo.
echo 🚀 Iniciando API REST...
echo 📚 Documentacion: http://localhost:8000/docs
echo ⏹️ Presiona Ctrl+C para detener
echo.
C:/Users/fifa2/AppData/Local/Programs/Python/Python313/python.exe run_api.py
goto end

:test
echo.
echo 🧪 Iniciando modo de pruebas...
echo.
C:/Users/fifa2/AppData/Local/Programs/Python/Python313/python.exe test_system.py
goto end

:docs
echo.
echo 📚 Abriendo documentacion de la API...
start http://localhost:8000/docs
echo.
echo La documentacion se abrira en tu navegador.
echo Si la API no esta ejecutandose, inicia la opcion 2 primero.
pause
goto start

:install
echo.
echo 📦 Instalando/Actualizando dependencias...
echo.
C:/Users/fifa2/AppData/Local/Programs/Python/Python313/python.exe -m pip install --upgrade pip
C:/Users/fifa2/AppData/Local/Programs/Python/Python313/python.exe -m pip install -r requirements.txt
echo.
echo ✅ Dependencias actualizadas!
pause
goto start

:exit
echo.
echo 👋 ¡Hasta luego!
exit

:end
echo.
echo 🏁 Proceso terminado.
pause

:start
goto start