@echo off
color 0f
echo ==========================================
echo      REPARACION DEL SISTEMA REN
echo ==========================================
echo.

echo [1/4] Deteniendo colectores antiguos...
taskkill /f /im powershell.exe >nul 2>&1

echo [2/4] Actualizando archivos del Servidor XAMPP...
if not exist "C:\xampp\htdocs\ren_monitor" mkdir "C:\xampp\htdocs\ren_monitor"
if not exist "C:\xampp\htdocs\ren_monitor\img" mkdir "C:\xampp\htdocs\ren_monitor\img"

copy /y "%~dp0api_ingest.php" "C:\xampp\htdocs\ren_monitor\"
copy /y "%~dp0api_read.php" "C:\xampp\htdocs\ren_monitor\"
copy /y "%~dp0db_config.php" "C:\xampp\htdocs\ren_monitor\"
copy /y "%~dp0DashboardREN.html" "C:\xampp\htdocs\ren_monitor\"
copy /y "%~dp0img\*.*" "C:\xampp\htdocs\ren_monitor\img\"

echo [3/4] Reiniciando Colector de Datos...
start "REN MIKROTIK COLLECTOR" python "%~dp0ren_monitor_backend.py"

echo [4/4] Abriendo Dashboard...
start "" "%~dp0DashboardREN.html"

echo.
echo ==========================================
echo      SISTEMA REPARADO Y REINICIADO
echo ==========================================
echo Por favor verifique que la ventana negra diga "SYNC" en verde.
echo.
pause
