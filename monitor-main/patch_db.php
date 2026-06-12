<?php
require 'db_config.php';
$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error)
    die("Conexión fallida: " . $conn->connect_error);

// 1. Añadir columnas para el Ranking y Seguridad en router_stats
$sql_alter = "ALTER TABLE router_stats 
              ADD COLUMN IF NOT EXISTS firewall_drops_total BIGINT DEFAULT 0,
              ADD COLUMN IF NOT EXISTS top_consumers TEXT AFTER vpn_profiles_detail";

if ($conn->query($sql_alter)) {
    echo "Esquema de router_stats actualizado con éxito.\n";
} else {
    echo "Error actualizando esquema: " . $conn->error . "\n";
}

$conn->close();
?>