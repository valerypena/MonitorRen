<?php
// API INGEST (Recibe datos del PowerShell)
header("Content-Type: application/json");
require 'db_config.php';

$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error) {
    die(json_encode(["error" => "Connection failed: " . $conn->connect_error]));
}

// Leer JSON
$json = file_get_contents('php://input');
file_put_contents('debug_payload.txt', $json); // DEBUG
$data = json_decode($json, true);

if (!$data) {
    die(json_encode(["error" => "No JSON received"]));
}

// Prepare Statement
$stmt = $conn->prepare("INSERT INTO router_stats (
    created_at,
    cpu_load, free_memory, total_memory, hdd_free, hdd_total, temperature, voltage, uptime,
    dhcp_leases, queue_count, wan_drops, sfp_rx_power, log_message,
    wan1_tx, wan1_rx, wan2_tx, wan2_rx,
    vpn_count, vpn_l2tp, vpn_ovpn, vpn_sstp, vpn_pptp,
    ping_avg_ms, ping_loss_percent, vpn_profiles_detail,
    firewall_drops_total, top_consumers, active_connections, gateway_ping, interface_errors
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)");

// Use provided time or fallback
$created_at = isset($data['created_at']) ? $data['created_at'] : date("Y-m-d H:i:s");

$vpn_detail = isset($data['vpn_profiles_detail']) ? json_encode($data['vpn_profiles_detail']) : "{}";
$top_consumers = isset($data['top_consumers']) ? json_encode($data['top_consumers']) : "[]";
$interface_errors = isset($data['interface_errors']) ? json_encode($data['interface_errors']) : "{}";
$active_conns = isset($data['active_connections']) ? $data['active_connections'] : 0;
$gw_ping = isset($data['gateway_ping']) ? $data['gateway_ping'] : 0;

// Bind params 
$stmt->bind_param(
    "sssssssdsiiidssssssiiiissssiis",
    $created_at,
    $data['cpu_load'],
    $data['free_memory'],
    $data['total_memory'],
    $data['hdd_free'],
    $data['hdd_total'],
    $data['temperature'],
    $data['voltage'],
    $data['uptime'],
    $data['dhcp_leases'],
    $data['queue_count'],
    $data['wan_drops'],
    $data['sfp_rx_power'],
    $data['log_message'],
    $data['wan1_tx'],
    $data['wan1_rx'],
    $data['wan2_tx'],
    $data['wan2_rx'],
    $data['vpn_count'],
    $data['vpn_l2tp'],
    $data['vpn_ovpn'],
    $data['vpn_sstp'],
    $data['vpn_pptp'],
    $data['ping_avg_ms'],
    $data['ping_loss_percent'],
    $vpn_detail,
    $data['firewall_drops_total'],
    $top_consumers,
    $active_conns,
    $gw_ping,
    $interface_errors
);

if ($stmt->execute()) {
    $last_id = $stmt->insert_id;
    echo json_encode(["status" => "success", "id" => $last_id]);

    // --- ALERT LOGIC (ISO 9001 Evidence) ---
    // Check for Critical Conditions
    $alertType = "";
    $alertMsg = "";
    $severity = "";

    // 1. Connectivity Loss
    if ($data['wan_drops'] > 0 || $data['ping_loss_percent'] > 50) {
        $alertType = "Connectivity";
        $severity = "Critical";
        $alertMsg = "Caída de conectividad detectada. Drops: " . $data['wan_drops'] . ", Loss: " . $data['ping_loss_percent'] . "%";
    }
    // 2. High Latency
    elseif ($data['ping_avg_ms'] > 150) {
        $alertType = "High Latency";
        $severity = "Warning";
        $alertMsg = "Latencia alta detectada: " . $data['ping_avg_ms'] . "ms";
    }
    // 3. Hardware Stress
    elseif ($data['cpu_load'] > 90) {
        $alertType = "Hardware Stress";
        $severity = "Warning";
        $alertMsg = "CPU Load Critical: " . $data['cpu_load'] . "%";
    }
    // 4. Unusual Bandwidth Consumption (e.g. > 50Mbps on WAN1)
    elseif ($data['wan1_rx'] > 50000000) {
        $alertType = "Traffic Spike";
        $severity = "Warning";
        $alertMsg = "Consumo inusual detectado en WAN1: " . round($data['wan1_rx'] / 1000000, 2) . " Mbps";
    }
    // 5. Unusual Number of People/Devices (e.g. > 100)
    elseif ($data['active_connections'] > 100) {
        $alertType = "User Count";
        $severity = "Warning";
        $alertMsg = "Número inusual de conexiones activas: " . $data['active_connections'];
    }

    if ($alertType != "") {
        // Insert Alert avoiding duplicates (Debounce could be added here in future)
        // For now, straightforward insert
        $alertStmt = $conn->prepare("INSERT INTO system_alerts (alert_type, severity, message) VALUES (?, ?, ?)");
        $alertStmt->bind_param("sss", $alertType, $severity, $alertMsg);
        $alertStmt->execute();
        $alertStmt->close();

        // 6. Email Notification (ISO 9001 Compliance)
        // Nota: Requiere configurar servidor SMTP en PHP.ini
        $to = "admin@empresa.com"; // CAMBIAR AQUÍ
        $subject = "[ALERT] REN Monitor - " . $alertType;
        $headers = "From: monitor@ren.com";

        // Intentar enviar correo si está configurado
        if (ini_get('SMTP')) {
            @mail($to, $subject, $alertMsg, $headers);
        }
    }

} else {
    echo json_encode(["error" => $stmt->error]);
}

$stmt->close();
$conn->close();
?>