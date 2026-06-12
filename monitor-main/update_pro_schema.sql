
-- Actualización para Soporte de Datos Reales de Red

USE ren_monitor;

-- 1. Tabla para Historial Real de Velocidad (Claro/Speedtest)
CREATE TABLE IF NOT EXISTS speed_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_mbps DOUBLE,
    upload_mbps DOUBLE,
    ping_ms DOUBLE,
    isp VARCHAR(100),
    server_location VARCHAR(100)
);

-- 2. Tabla para Inventario de Dispositivos (Usuarios conectados)
CREATE TABLE IF NOT EXISTS device_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mac_address VARCHAR(20) UNIQUE,
    ip_address VARCHAR(20),
    hostname VARCHAR(100),
    vendor VARCHAR(100),
    interface VARCHAR(50),
    is_online BOOLEAN DEFAULT TRUE,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Tabla para Centralización de Logs (Rsyslog alternativo)
CREATE TABLE IF NOT EXISTS network_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    topic VARCHAR(50),
    message TEXT,
    severity VARCHAR(20) DEFAULT 'info'
);

-- 4. Modificar tabla router_stats para incluir más detalle si es necesario
-- (Ya tenemos la base, pero añadimos índices para reportes rápidos)
CREATE INDEX IF NOT EXISTS idx_speed_time ON speed_history(created_at);
CREATE INDEX IF NOT EXISTS idx_device_ip ON device_inventory(ip_address);
CREATE INDEX IF NOT EXISTS idx_logs_time ON network_logs(created_at);
