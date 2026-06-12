-- Migración para Telemetría Tier 3
USE ren_monitor;

ALTER TABLE router_stats 
ADD COLUMN IF NOT EXISTS active_connections INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS gateway_ping DOUBLE DEFAULT 0,
ADD COLUMN IF NOT EXISTS interface_errors TEXT,
ADD COLUMN IF NOT EXISTS firewall_drops_total BIGINT DEFAULT 0,
ADD COLUMN IF NOT EXISTS top_consumers TEXT;
