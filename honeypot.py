#!/usr/bin/env python3
"""
HoneyPing - simple honeypot logger (safe, minimal).
Listens on specified ports, accepts connections, records remote IP,
timestamp, and first N bytes (if any) to a log file. Does NOT execute
remote input or provide shells.
"""
import socket, threading, datetime, os, json

PORTS = [2222, 8080]            # change or restrict for your lab
BIND_ADDR = '0.0.0.0'           # or '127.0.0.1' for local-only testing
LOG_DIR = "logs"
CAP_BYTES = 256                 # capture up to N bytes

os.makedirs(LOG_DIR, exist_ok=True)

def handle_client(conn, addr, listen_port):
    ip, port = addr[0], addr[1]
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    try:
        conn.settimeout(3.0)
        data = conn.recv(CAP_BYTES)
    except Exception:
        data = b""
    finally:
        try:
            conn.close()
        except Exception:
            pass
    entry = {
        "timestamp": timestamp,
        "listen_port": listen_port,
        "remote_ip": ip,
        "remote_port": port,
        "first_bytes": data.decode('utf-8', errors='replace')
    }
    fname = os.path.join(LOG_DIR, f"{datetime.date.today().isoformat()}.log")
    with open(fname, "a") as fh:
        fh.write(json.dumps(entry) + "\\n")
    print(f"[{timestamp}] {ip}:{port} -> port {listen_port} (logged)")

def start_listener(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((BIND_ADDR, port))
    s.listen(5)
    print(f"Honeypot listening on {BIND_ADDR}:{port}")
    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr, port), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("Listener shutting down")
    finally:
        s.close()

def generate_report(out="reports/honeypot_report.html"):
    import glob
    import jinja2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    logs = []
    for f in sorted(glob.glob(os.path.join(LOG_DIR,"*.log"))):
        with open(f) as fh:
            for line in fh:
                try:
                    logs.append(json.loads(line.strip()))
                except Exception:
                    continue
    template = jinja2.Template('''<html><head><meta charset="utf-8"><title>HoneyPing Report</title>
    <style>body{background:#000;color:#39ff14;font-family:monospace}table{width:100%;border-collapse:collapse}
    td,th{border:1px solid #222;padding:6px;color:#fff}</style></head><body>
    <h1>HoneyPing - Connection Log</h1><table><tr><th>Time (UTC)</th><th>Listen Port</th><th>Remote IP</th><th>Remote Port</th><th>Payload (first bytes)</th></tr>
    {% for e in logs %}<tr><td>{{e.timestamp}}</td><td>{{e.listen_port}}</td><td>{{e.remote_ip}}</td><td>{{e.remote_port}}</td><td><pre>{{e.first_bytes}}</pre></td></tr>{% endfor %}
    </table></body></html>''')
    with open(out,"w") as fh:
        fh.write(template.render(logs=logs))
    print("Report generated:", out)

if __name__ == "__main__":
    import sys
    # start listeners in threads
    threads = []
    for p in PORTS:
        t = threading.Thread(target=start_listener, args=(p,), daemon=True)
        t.start()
        threads.append(t)
    print("HoneyPing started. Ctrl+C to stop. After stopping run: python honeypot.py --report")
    try:
        while True:
            for t in threads:
                if not t.is_alive():
                    raise SystemExit
            # keep main thread alive
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Stopping honeypot (Ctrl+C pressed)")
        generate_report()
        sys.exit(0)
