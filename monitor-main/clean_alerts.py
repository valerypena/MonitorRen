
import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "ren_monitor"
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE system_alerts")
    conn.commit()
    conn.close()
    print("SUCCESS: Alertas eliminadas.")
except Exception as e:
    print(f"ERROR: {e}")
