import sys
import pymysql

print("[TEST] Testing host='localhost' vs host='127.0.0.1' with user='root'...", flush=True)

for host in ["localhost", "127.0.0.1"]:
    for pwd in ["Omkar@123", "omkar@123", "root", "admin", "123456", ""]:
        try:
            conn = pymysql.connect(
                host=host,
                port=3306,
                user="root",
                password=pwd,
                connect_timeout=2
            )
            print(f"[FOUND SUCCESS!] Host={host}, Password={pwd or '(empty)'} worked!", flush=True)
            conn.close()
            sys.exit(0)
        except pymysql.err.OperationalError as e:
            code = e.args[0] if e.args else None
            # print only brief
            if code == 1045:
                # 1045 = bad password
                pass
            else:
                print(f"Host={host}, Error {code}: {e}", flush=True)
                break
        except Exception as e:
            print(f"Host={host}, Exception: {e}", flush=True)
            break

print("[TEST] Finished candidate checks. None of the default quick candidates matched.", flush=True)
