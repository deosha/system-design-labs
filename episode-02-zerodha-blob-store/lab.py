"""Episode 2 lab: hit the single-writer wall, shard and batch, then crash it.

  python3 lab.py wall    measure writes/s with config.py
  python3 lab.py crash   kill -9 mid-burst and count acknowledged writes that were lost
  python3 lab.py check   PASS if config.py is >= 4x faster than 1 shard / batch 1, and loses nothing on a crash
"""
import importlib, os, shutil, signal, subprocess, sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from blobstore import Store

VALUE = os.urandom(8_000)      # an 8 KB "chart layout"
CLIENTS = 16


def throughput(shards, batch, async_ack, seconds=4.0):
    d = tempfile.mkdtemp(prefix="blobs-")
    try:
        s = Store(d, shards, batch, async_ack)
        count = [0] * CLIENTS
        stop = time.time() + seconds
        def client(n):
            i = 0
            while time.time() < stop:
                s.put(f"user{n}:layout{i}", VALUE); i += 1
            count[n] = i
        ts = [threading.Thread(target=client, args=(n,)) for n in range(CLIENTS)]
        [t.start() for t in ts]; [t.join() for t in ts]
        return sum(count) / seconds
    finally:
        shutil.rmtree(d, ignore_errors=True)


def crash(shards, batch, async_ack, seconds=2.0):
    """Run a writer process, read its acknowledgements, kill -9 it, count what survived."""
    d = tempfile.mkdtemp(prefix="blobs-")
    code = (f"import sys; sys.path.insert(0, {HERE!r}); from blobstore import Store; import os\n"
            f"s = Store({d!r}, {shards}, {batch}, {async_ack}); v = os.urandom(8000)\n"
            "for i in range(10**9):\n    s.put(f'k{i}', v); print(i, flush=True)\n")
    p = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
    acked, t0 = -1, time.time()
    for line in p.stdout:
        acked = int(line)
        if time.time() - t0 > seconds:
            break
    os.kill(p.pid, signal.SIGKILL); p.wait()
    s = Store(d, shards, batch, False)
    lost = sum(1 for i in range(acked + 1) if s.get(f"k{i}") is None)
    shutil.rmtree(d, ignore_errors=True)
    return acked + 1, lost


def cfg():
    return importlib.import_module("config")


def main(mode):
    c = cfg()
    print(f"config: SHARDS={c.SHARDS} BATCH_SIZE={c.BATCH_SIZE} ASYNC_ACK={c.ASYNC_ACK}")
    if mode == "wall":
        print(f"{throughput(c.SHARDS, c.BATCH_SIZE, c.ASYNC_ACK):,.0f} writes/s")
    elif mode == "crash":
        acked, lost = crash(c.SHARDS, c.BATCH_SIZE, c.ASYNC_ACK)
        print(f"acknowledged {acked:,}, lost after kill -9: {lost:,}")
    elif mode == "check":
        base = throughput(1, 1, False)
        mine = throughput(c.SHARDS, c.BATCH_SIZE, c.ASYNC_ACK)
        acked, lost = crash(c.SHARDS, c.BATCH_SIZE, c.ASYNC_ACK)
        print(f"baseline (1 shard, batch 1): {base:,.0f} writes/s")
        print(f"your config:                 {mine:,.0f} writes/s  ({mine / base:.1f}x)")
        print(f"crash test: acknowledged {acked:,}, lost {lost:,}")
        if mine >= 4 * base and lost == 0:
            print("PASS: at least 4x faster, and no acknowledged write was lost")
            return 0
        print("FAIL: need at least 4x the baseline AND zero lost acknowledged writes")
        return 1
    else:
        print(__doc__); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
