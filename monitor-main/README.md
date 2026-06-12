# REN Enterprise Monitor v2.1 (Edición Unificada)

Sistema profesional de monitoreo de red y telemetría diseñado para infraestructura MikroTik. Esta versión unificada consolida servicios de backend, dashboards en tiempo real y reportes automatizados en una única solución portátil.

## 🚀 Características Principales

- **Dashboard en Tiempo Real**: Visualización de alta fidelidad de tráfico (WAN1/WAN2), latencia, pérdida de paquetes y salud del hardware (CPU, Temp, RAM).
- **Integración MikroTik**: Recolección directa de telemetría mediante la API de RouterOS.
- **Modo NOC Avanzado**: Vista optimizada para monitores grandes 📺 en Centros de Operaciones de Red.
- **Pruebas de SLA y Velocidad**: Seguimiento manual y automatizado de la velocidad de internet con historial detallado.
- **Reportes ISO 9001**: Generación de reportes visuales profesionales en PDF con un solo clic.
- **Cyber Armor**: Monitoreo de seguridad integrado y visualización de amenazas perimetrales.
- **Auto-Reparación**: Incluye `repair_system.bat` para refrescos automáticos del sistema y sincronización con XAMPP.

## 📂 Estructura del Proyecto

- `DashboardREN.html`: Dashboard principal de monitoreo empresarial.
- `ren_monitor_backend.py`: Motor Python para telemetría MikroTik y pruebas de velocidad.
- `api_ingest.php` / `api_read.php`: Puente de datos entre el backend/frontend y MySQL.
- `database_complete.sql`: Esquema de base de datos consolidado y configuración inicial.
- `db_config.php`: Credenciales centralizadas de la base de datos.
- `repair_system.bat`: Script de mantenimiento y despliegue automatizado.
- `instalar.bat`: Script de instalación automática y configuración de inicio.
- `MikrotikCollector.ps1`: Colector heredado en PowerShell (alternativa al motor Python).

## 🚀 Guía Rápida de Instalación / Replicación

Para replicar este proyecto en una nueva máquina desde cero (o clonando desde GitHub), sigue estos pasos:

### 1. Requisitos Previos
- **XAMPP / Servidor Web**: Necesitas tener Apache y MySQL corriendo.
- **Python 3.8+**: Asegúrate de tener Python instalado y agregado al PATH.

### 2. Instalación Paso a Paso

1.  **Clonar/Descargar Repositorio**:
    Coloca el proyecto en una carpeta accesible. Si usas XAMPP, idealmente un enlace simbólico o copia en `htdocs` puede ser útil, pero el sistema incluye scripts para ello.

2.  **Configurar Base de Datos Automáticamente**:
    Hemos incluido un script para facilitar esto. Abre una terminal en la carpeta `ren_monitor` y ejecuta:
    ```bash
    pip install pymysql requests routeros_api
    python setup_db.py
    ```
    *Sigue las instrucciones en pantalla. Por defecto usa usuario `root` sin contraseña (común en XAMPP).*

3.  **Desplegar Dashboard**:
    Ejecuta el script de reparación/despliegue que copiará los archivos necesarios a tu servidor web local (XAMPP):
    ```batch
    repair_system.bat
    ```

4.  **Verificar Logo**:
    Asegúrate de colocar el logo de tu empresa en `ren_monitor/img/logo.png`.

5.  **Iniciar Backend**:
    ```bash
    python ren_monitor_backend.py
    ```

---

### Configuración de Credenciales
Actualiza `ren_monitor_backend.py` (líneas 11-13) con la IP, usuario y contraseña de tu MikroTik principal.


## 🖥️ Uso

- **Lanzar Backend**: Simplemente ejecuta `python ren_monitor_backend.py` o usa `repair_system.bat`.
- **Ver Dashboard**: Abre `DashboardREN.html` en cualquier navegador moderno o navega a `http://localhost/ren_monitor/DashboardREN.html` si lo hospedas vía Apache.
- **Modo NOC**: Presiona el botón 📺 en el encabezado del dashboard para la vista de monitoreo en pantalla completa.

## ❓ Preguntas Frecuentes y Solución de Problemas (FAQ)

**1. El Dashboard muestra "CONNECTION LOST"**
- Verifica que Apache y MySQL estén iniciados en XAMPP.
- Asegúrate de que los archivos `api_read.php` y `db_config.php` estén en `C:\xampp\htdocs\ren_monitor\`.

**2. No se ven datos de tráfico en los gráficos**
- Revisa la consola del backend (`python`). Si dice "Error de conexión", verifica que el MikroTik tenga la API habilitada (`/ip service enable api`).
- Confirma que las credenciales en `ren_monitor_backend.py` sean correctas.

**3. ¿Cómo cambio el intervalo de Speedtest?**
- En `ren_monitor_backend.py`, busca la línea que dice `now - last_speedtest > 3600` y cambia el 3600 (1 hora) por el tiempo en segundos que desees.

**4. ¿Puedo monitorear más de 2 WANs?**
- Sí, puedes editar el archivo `ren_monitor_backend.py` en la función `collect_telemetry` para agregar más nombres de interfaces y mapearlas al payload.

## 📘 Más Información
Para detalles técnicos profundos, consulta el archivo [DOCUMENTATION.md](./DOCUMENTATION.md).

---
*Desarrollado por REN Enterprise Monitoring Systems.*
