
try:
    import routeros_api
    import pymysql
    import speedtest
    print("Dependencies OK")
except ImportError as e:
    print(f"Missing dependency: {e}")
