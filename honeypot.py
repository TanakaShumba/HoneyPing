#!/usr/bin/env python3
import socket, threading, datetime, os, json, jinja2

PORTS = [2222, 8080]
LOG_DIR = "logs"; os.makedirs(LOG_DIR, exist_ok=True)

def handle(conn, addr, port):
    ip = addr[0]; now = datetime.datetime.utcnow().isoformat()+"Z"
    try:
        conn.settimeout(3); data = conn.recv(200)
    except: data = b""
    finally: conn.close()
    entry = {"time": now, "port": port, "ip": ip, "data": data.decode(errors='ignore')}
    open(os.path.join(LOG_DIR, f"{datetime.date.today()}.log"), "a").write(json.dumps(entry)+"\n")
    print(f"[{now}] {ip} hit port {port}")

def listen(port):
    s = socket.socket(); s.bind(("0.0.0.0", port)); s.listen(5)
    print(f"Listening on {port}...")
    while True:
        c,a = s.accept()
        threading.Thread(target=handle, args=(c,a,port), daemon=True).start()

if __name__ == "__main__":
    for p in PORTS:
        threading.Thread(target=listen, args=(p,), daemon=True).start()
    input("HoneyPing running... press Enter to stop.")
