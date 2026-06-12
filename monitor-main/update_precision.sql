-- MODIFICAR COLUMNAS PARA SOPORTAR DECIMALES (PRECISION)
USE ren_monitor;

ALTER TABLE router_stats MODIFY COLUMN ping_avg_ms FLOAT DEFAULT 0;
ALTER TABLE router_stats MODIFY COLUMN ping_loss_percent FLOAT DEFAULT 0;

SELECT "Columnas actualizadas a FLOAT para mayor precision." as Mensaje;
