-- Add columns for Advanced Mikrotik Metrics
alter table router_stats
add column wan_drops int default 0,      -- Paquetes perdidos (WAN1 + WAN2)
add column sfp_rx_power float,           -- Potencia óptica (dBm)
add column log_message text,             -- Último log crítico
add column queue_count int default 0;    -- Número de colas saturadas (Queues)
