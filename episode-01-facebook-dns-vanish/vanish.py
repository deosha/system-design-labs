"""Lab: how healthy DNS servers can make a whole company vanish.

Two authoritative DNS "sites" answer for shop.example. Each site checks that it can
reach the data centre (the "backbone"). If it can't, it withdraws itself, the way
Meta's DNS sites withdrew their BGP routes on 4 October 2021.

Usage:
  python3 vanish.py withdraw      # the 2021 design: every site withdraws together
  python3 vanish.py failstatic    # run your fix (edit policy.py)
  python3 vanish.py check         # PASS if shop.example survives the backbone loss
"""
import socket, sys, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from dnslib import A, DNSRecord, QTYPE, RR
from dnslib.server import BaseResolver, DNSLogger, DNSServer

import policy

ZONE, IP = "shop.example.", "10.0.2.10"
SITES = {"site-a": 5301, "site-b": 5302}


class Backbone(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a):
        pass


def backbone_up():
    try:
        socket.create_connection(("127.0.0.1", 8053), timeout=0.3).close()
        return True
    except OSError:
        return False


class Site(BaseResolver):
    def __init__(self, name):
        self.name, self.healthy, self.withdrawn = name, True, False

    def can_answer(self):
        """Self-test: does this site still hold a valid answer for the shop?"""
        reply = self.resolve(DNSRecord.question("shop.example"), None)
        return bool(reply.rr)

    def check(self):
        self.healthy = backbone_up()
        self.withdrawn = not policy.should_answer(self.name, self.healthy, self.can_answer(), SITE_STATE)

    def resolve(self, request, handler):
        reply = request.reply()
        if request.q.qname == ZONE and QTYPE[request.q.qtype] == "A":
            reply.add_answer(RR(ZONE, QTYPE.A, rdata=A(IP), ttl=60))
        return reply


SITE_STATE = {}


def run_site(name, port):
    site = Site(name)
    SITE_STATE[name] = site
    srv = DNSServer(site, port=port, address="127.0.0.1", logger=DNSLogger("-request,-reply,-truncated,-error,-recv,-send,-data", False))
    srv.start_thread()

    def loop():
        while True:
            site.check()
            if site.withdrawn and srv.isAlive():
                srv.stop()          # stop announcing: unreachable, though the process is alive
            time.sleep(0.5)
    threading.Thread(target=loop, daemon=True).start()


def ask():
    for name, port in SITES.items():
        try:
            r = DNSRecord.parse(DNSRecord.question("shop.example").send("127.0.0.1", port, timeout=1))
            return f"shop.example -> {r.rr[0].rdata} (answered by {name})"
        except Exception:
            continue
    return "shop.example -> NO ANSWER from any DNS server"


def status():
    return ", ".join(f"{n}: process running, {'withdrawn' if s.withdrawn else 'answering'}" for n, s in SITE_STATE.items())


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "withdraw"
    policy.MODE = "fix" if mode in ("failstatic", "check") else mode
    bb = HTTPServer(("127.0.0.1", 8053), Backbone)
    threading.Thread(target=bb.serve_forever, daemon=True).start()
    for n, p in SITES.items():
        run_site(n, p)
    time.sleep(1.5)
    print("[backbone up]  ", ask())
    print("               ", status())
    bb.shutdown(); bb.server_close()
    print("... maintenance command: backbone disconnected")
    time.sleep(2.0)
    print("[backbone down]", ask())
    print("               ", status())
    if mode == "check":
        ok = "NO ANSWER" not in ask()
        print("PASS: shop.example still resolves with the backbone down" if ok else "FAIL: shop.example vanished")
        sys.exit(0 if ok else 1)
