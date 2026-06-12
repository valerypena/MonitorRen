<?php
require 'db_config.php';
$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error)
    die("Conexión fallida: " . $conn->connect_error);

$sql = file_get_contents('update_tier3.sql');

if ($conn->multi_query($sql)) {
    do {
        if ($result = $conn->store_result()) {
            $result->free();
        }
    } while ($conn->next_result());
    echo "Base de datos actualizada con éxito.";
} else {
    echo "Error ejecutando SQL: " . $conn->error;
}
$conn->close();
?>