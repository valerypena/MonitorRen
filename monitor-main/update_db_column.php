<?php
$host = "localhost";
$user = "root";
$pass = "";
$db = "ren_monitor";

$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Check if column exists
$check = $conn->query("SHOW COLUMNS FROM router_stats LIKE 'vpn_profiles_detail'");
if ($check->num_rows == 0) {
    echo "Column 'vpn_profiles_detail' missing. Adding...<br>";
    $sql = "ALTER TABLE router_stats ADD COLUMN vpn_profiles_detail TEXT";
    if ($conn->query($sql) === TRUE) {
        echo "Column added successfully";
    } else {
        echo "Error adding column: " . $conn->error;
    }
} else {
    echo "Column 'vpn_profiles_detail' already exists.";
}

$conn->close();
?>