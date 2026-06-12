
-- Base de Datos
CREATE DATABASE IF NOT EXISTS ren_monitor;
USE ren_monitor;

-- Tabla de Estadísticas
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
    
    -- Latencia (Nuevo)
    ping_avg_ms INT DEFAULT 0,
    ping_loss_percent INT DEFAULT 0,
    
    -- VPN Profiles Detail (JSON)
    vpn_profiles_detail TEXT
);

-- Indices para velocidad
CREATE INDEX idx_created_at ON router_stats(created_at);

-- Tabla de Alertas del Sistema (ISO 9001 Evidencia)
CREATE TABLE IF NOT EXISTS system_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(50), -- 'Connectivity', 'High Latency', 'Saturación'
    severity VARCHAR(20),   -- 'Warning', 'Critical'
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);

CREATE INDEX idx_alert_time ON system_alerts(created_at);
