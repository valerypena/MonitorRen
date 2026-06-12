import pymysql
import sys
import os

def setup_database():
    print("==========================================")
    print("   REN ENTERPRISE MONITOR - CONFIG DB")
    print("==========================================\n")

    # Default configuration
    default_host = "localhost"
    default_user = "root"
    default_pass = ""
    
    print("Por favor ingrese sus credenciales de MySQL.")
    print(f"Presione ENTER para usar los valores por defecto [{default_host} / {default_user} / (sin contraseña)]\n")

    host = input(f"Servidor (Host) [{default_host}]: ").strip() or default_host
    user = input(f"Usuario [{default_user}]: ").strip() or default_user
    password = input("Contraseña: ").strip()

    print(f"\nConectando a MySQL en {host} como {user}...")

    try:
        # Connect to MySQL Server (no DB selected yet)
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("Conexión exitosa con el servidor.")

        try:
            with connection.cursor() as cursor:
                # Read SQL file
                sql_file_path = os.path.join(os.path.dirname(__file__), 'database_complete.sql')
                if not os.path.exists(sql_file_path):
                    print(f"ERROR: No se pudo encontrar {sql_file_path}")
                    return

                print(f"Leyendo esquema desde {sql_file_path}...")
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()

                # Split commands (simple split by semicolon, might need robust parsing if complex)
                # For this specific file, statements are clearly delimited.
                # However, pymysql can't execute multiple statements in one go easily without special flags.
                # A safer approach for a setup script is to parse and execute.
                # But database_complete.sql is relatively simple.
                
                # Let's try to execute specialized logic for this file
                commands = sql_content.split(';')
                
                count = 0
                for command in commands:
                    skipped_empty = command.strip()
                    if skipped_empty:
                        try:
                            cursor.execute(skipped_empty)
                            count += 1
                        except Exception as e:
                            print(f"ADVERTENCIA ejecutando comando: {e}")
                            print(f"Comando parcial: {skipped_empty[:50]}...")

                print(f"\n¡ÉXITO! Se ejecutaron {count} sentencias SQL.")
                print("La base de datos 'ren_monitor' debería estar creada/actualizada ahora.")

        finally:
            connection.close()

    except pymysql.MySQLError as e:
        print(f"\nERROR CRÍTICO: No se pudo conectar a MySQL.")
        print(f"Detalles: {e}")
        print("\nPor favor verifique que XAMPP/MySQL esté corriendo y las credenciales sean correctas.")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
