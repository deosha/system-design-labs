"""A tiny blob store on SQLite, shaped like Blobasaur: N shard files, one writer
thread per shard, optional batched commits, optional async acknowledgement.
You don't need to edit this file. Change config.py instead."""
import hashlib, os, queue, sqlite3, threading


class Store:
    def __init__(self, data_dir, shards=1, batch_size=1, async_ack=False):
        os.makedirs(data_dir, exist_ok=True)
        self.shards, self.batch_size, self.async_ack = shards, batch_size, async_ack
        self.paths = [os.path.join(data_dir, f"shard-{i}.db") for i in range(shards)]
        self.queues = [queue.Queue(maxsize=4096) for _ in range(shards)]
        for p in self.paths:
            c = sqlite3.connect(p)
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("CREATE TABLE IF NOT EXISTS blobs (key TEXT PRIMARY KEY, value BLOB)")
            c.commit(); c.close()
        self.threads = [threading.Thread(target=self._writer, args=(i,), daemon=True) for i in range(shards)]
        for t in self.threads:
            t.start()

    def shard_for(self, key):
        return int.from_bytes(hashlib.blake2b(key.encode(), digest_size=8).digest(), "big") % self.shards

    def put(self, key, value):
        done = None if self.async_ack else threading.Event()
        self.queues[self.shard_for(key)].put((key, value, done))
        if done:
            done.wait()          # durable: return only after the commit

    def get(self, key):
        c = sqlite3.connect(self.paths[self.shard_for(key)])
        row = c.execute("SELECT value FROM blobs WHERE key=?", (key,)).fetchone()
        c.close()
        return row[0] if row else None

    def _writer(self, i):
        c = sqlite3.connect(self.paths[i], check_same_thread=False)
        c.execute("PRAGMA synchronous=FULL")    # every commit is fsynced
        q = self.queues[i]
        while True:
            batch = [q.get()]
            while len(batch) < self.batch_size:
                try:
                    batch.append(q.get_nowait())
                except queue.Empty:
                    break
            c.executemany("INSERT OR REPLACE INTO blobs VALUES (?, ?)", [(k, v) for k, v, _ in batch])
            c.commit()
            for _, _, done in batch:
                if done:
                    done.set()
