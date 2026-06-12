-- ==========================================
-- SCRIPT DE ACTUALIZACION COMPLETA STV-IT
-- ==========================================
-- Ejecuta este script en phpMyAdmin o Workbench
-- para poner tu base de datos al día.

CREATE DATABASE IF NOT EXISTS ren_monitor;
USE ren_monitor;

-- 1. Asegurar que la tabla principal existe
CREATE TABLE IF NOT EXISTS router_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Agregar columnas faltantes en router_stats (Si fallan por "Duplicate column name" es SEGURO ignorarlo)
-- Intento agregar columnas de Hardware
ALTER TABLE router_stats ADD COLUMN cpu_load INT;
ALTER TABLE router_stats ADD COLUMN free_memory BIGINT;
ALTER TABLE router_stats ADD COLUMN total_memory BIGINT;
ALTER TABLE router_stats ADD COLUMN hdd_free BIGINT;
ALTER TABLE router_stats ADD COLUMN hdd_total BIGINT;
ALTER TABLE router_stats ADD COLUMN temperature INT;
ALTER TABLE router_stats ADD COLUMN voltage INT;
ALTER TABLE router_stats ADD COLUMN uptime VARCHAR(50);

-- Intento agregar columnas de Red
ALTER TABLE router_stats ADD COLUMN dhcp_leases INT;
ALTER TABLE router_stats ADD COLUMN queue_count INT;
ALTER TABLE router_stats ADD COLUMN wan_drops INT;
ALTER TABLE router_stats ADD COLUMN sfp_rx_power DOUBLE;
ALTER TABLE router_stats ADD COLUMN log_message TEXT;

-- Intento agregar columnas WAN
ALTER TABLE router_stats ADD COLUMN wan1_tx BIGINT;
ALTER TABLE router_stats ADD COLUMN wan1_rx BIGINT;
ALTER TABLE router_stats ADD COLUMN wan2_tx BIGINT;
ALTER TABLE router_stats ADD COLUMN wan2_rx BIGINT;

-- Intento agregar columnas VPN
ALTER TABLE router_stats ADD COLUMN vpn_count INT;
ALTER TABLE router_stats ADD COLUMN vpn_l2tp INT;
ALTER TABLE router_stats ADD COLUMN vpn_ovpn INT;
ALTER TABLE router_stats ADD COLUMN vpn_sstp INT;
ALTER TABLE router_stats ADD COLUMN vpn_pptp INT;

-- 3. NUEVAS COLUMNAS (Lo critico para esta actualizacion)
ALTER TABLE router_stats ADD COLUMN ping_avg_ms INT DEFAULT 0;
ALTER TABLE router_stats ADD COLUMN ping_loss_percent INT DEFAULT 0;

-- 4. Indices
CREATE INDEX idx_created_at ON router_stats(created_at);

-- 5. NUEVA TABLA DE ALERTAS (ISO 9001)
CREATE TABLE IF NOT EXISTS system_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type VARCHAR(50), 
    severity VARCHAR(20),   
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);

CREATE INDEX idx_alert_time ON system_alerts(created_at);

-- Confirmación
SELECT "La base de datos ha sido actualizada exitosamente." as Mensaje;
