import sys
import pymysql

print("[TEST] Python executable:", sys.executable, flush=True)
print("[TEST] Attempting connection to 127.0.0.1:3306 with user='root'...", flush=True)

try:
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="Omkar@123",
        connect_timeout=3
    )
    print("[TEST] SUCCESS! Connected to MySQL 8.0 server.", flush=True)
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION() AS ver;")
        res = cursor.fetchone()
        print("[TEST] Server Version:", res, flush=True)
    conn.close()
except pymysql.err.OperationalError as op_err:
    code = op_err.args[0] if op_err.args else None
    print(f"[TEST] OPERATIONAL ERROR (Code {code}): {op_err}", flush=True)
except Exception as ex:
    print(f"[TEST] EXCEPTION: {type(ex).__name__}: {ex}", flush=True)
