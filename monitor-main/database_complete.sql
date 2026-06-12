-- ==========================================
-- REN MONITOR - DATABASE COMPLETE SCHEMA
-- ==========================================

CREATE DATABASE IF NOT EXISTS ren_monitor;
USE ren_monitor;

-- 1. Tabla de Estadísticas (router_stats)
CREATE TABLE IF NOT EXISTS router_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Hardware
    cpu_load INT,
    free_memory BIGINT,
    total_memory BIGINT,
    hdd_free BIGINT,
    hdd_total BIGINT,
    temperature INT,
    voltage INT,
    uptime VARCHAR(50),
    
    -- Network
    dhcp_leases INT,
    queue_count INT,
    wan_drops INT,
    sfp_rx_power DOUBLE,
    log_message TEXT,
    
    -- WAN 1 (Claro)
    wan1_tx BIGINT,
    wan1_rx BIGINT,
    
    -- WAN 2 (Movistar)
    wan2_tx BIGINT,
    wan2_rx BIGINT,
    
    -- VPN Breakdown
    vpn_count INT,
    vpn_l2tp INT,
    vpn_ovpn INT,
    vpn_sstp INT,
    vpn_pptp INT,
    
    -- Latencia
    ping_avg_ms DOUBLE DEFAULT 0,
    ping_loss_percent INT DEFAULT 0,
    
    -- VPN Profiles Detail & Extended Data (JSON)
    vpn_profiles_detail TEXT,
    firewall_drops_total BIGINT DEFAULT 0,
    top_consumers TEXT,
    active_connections INT DEFAULT 0,
    gateway_ping DOUBLE DEFAULT 0,
    interface_errors TEXT
);

CREATE INDEX idx_created_at ON router_stats(created_at);

-- 2. Tabla de Alertas del Sistema (ISO 9001)
CREATE TABLE IF NOT EXISTS system_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(50), 
    severity VARCHAR(20),   
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);

CREATE INDEX idx_alert_time ON system_alerts(created_at);

-- 3. Tabla para Historial Real de Velocidad (Speedtest)
CREATE TABLE IF NOT EXISTS speed_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_mbps DOUBLE,
    upload_mbps DOUBLE,
    ping_ms DOUBLE,
    isp VARCHAR(100),
    server_location VARCHAR(100)
);

CREATE INDEX idx_speed_time ON speed_history(created_at);

-- 4. Tabla para Inventario de Dispositivos
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

CREATE INDEX idx_device_ip ON device_inventory(ip_address);

-- 5. Tabla para Centralización de Logs
CREATE TABLE IF NOT EXISTS network_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    topic VARCHAR(50),
    message TEXT,
    severity VARCHAR(20) DEFAULT 'info'
);

CREATE INDEX idx_logs_time ON network_logs(created_at);
