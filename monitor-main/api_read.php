<?php
// API READ (Lee datos para el Dashboard) - NO CACHE
header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");
header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");

require 'db_config.php';

$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error) {
    die(json_encode(["error" => "Conn failed"]));
}

// --- AUTO-MIGRATE (Temporary Fix) ---
// Check and Add Column if missing
$colCheck = $conn->query("SHOW COLUMNS FROM router_stats LIKE 'vpn_profiles_detail'");
if ($colCheck && $colCheck->num_rows == 0) {
    $conn->query("ALTER TABLE router_stats ADD COLUMN vpn_profiles_detail TEXT");
}
// ------------------------------------

// Params
$mode = isset($_GET['mode']) ? $_GET['mode'] : 'live'; // 'live', 'history', 'alerts'
$startDate = isset($_GET['start']) ? $_GET['start'] : null;
$endDate = isset($_GET['end']) ? $_GET['end'] : null;

$data = [];

// MODE: LIVE (Last 60 records for real-time graphs)
if ($mode == 'live') {
    $limit = 60;
    $sql = "SELECT * FROM router_stats ORDER BY created_at DESC LIMIT $limit";
    $result = $conn->query($sql);
    while ($r = $result->fetch_assoc()) {
        $data[] = $r;
    }
}

// MODE: HISTORY (Filtered by Date Range - Max 5000 rows to prevent crash)
elseif ($mode == 'history') {
    if (!$startDate || !$endDate) {
        $data = ["error" => "Missing start/end dates for history mode"];
    } else {
        $sql = "SELECT * FROM router_stats WHERE created_at BETWEEN '$startDate 00:00:00' AND '$endDate 23:59:59' ORDER BY created_at ASC LIMIT 5000";
        $result = $conn->query($sql);
        while ($r = $result->fetch_assoc()) {
            $data[] = $r;
        }
    }
}

// MODE: ALERTS (Active/Recent alerts)
elseif ($mode == 'alerts') {
    $limit = 20;
    $sql = "SELECT * FROM system_alerts ORDER BY created_at DESC LIMIT $limit";
    $result = $conn->query($sql);
    while ($r = $result->fetch_assoc()) {
        $data[] = $r;
    }
}

// MODE: SPEEDTEST (Últimos resultados de velocidad real)
elseif ($mode == 'speedtest') {
    $limit = 10;
    $sql = "SELECT * FROM speed_history ORDER BY created_at DESC LIMIT $limit";
    $result = $conn->query($sql);
    while ($r = $result->fetch_assoc()) {
        $data[] = $r;
    }
}

// MODE: DEVICES (Lista de dispositivos reales detectados)
elseif ($mode == 'devices') {
    $sql = "SELECT * FROM device_inventory WHERE is_online = 1 ORDER BY last_seen DESC";
    $result = $conn->query($sql);
    while ($r = $result->fetch_assoc()) {
        $data[] = $r;
    }
}

echo json_encode($data);

$conn->close();
?>