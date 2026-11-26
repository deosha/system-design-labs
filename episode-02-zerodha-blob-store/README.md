# Episode 2 lab: storage that hits a wall

[![labs](https://github.com/deosha/system-design-labs/actions/workflows/labs.yml/badge.svg)](https://github.com/deosha/system-design-labs/actions/workflows/labs.yml)

Zerodha keeps Kite's chart layouts, indicators and drawings as small blobs, and about half
the traffic is writes. Their old store ran on one machine and hit a wall, so they built
[Blobasaur](https://github.com/iamd3vil/blobasaur): SQLite split into shards, one writer
per shard, batched commits, and an optional fast mode that acknowledges writes before
they reach disk.

In this lab you build the same idea in miniature, measure it, and then crash it.

**Time:** about 20 minutes · **Needs:** Python 3.10+, nothing else · **Runs:** locally, in temp folders

## The setup

```
client ─┐                ┌─ queue ─▶ writer ─▶ shard-0.db
client ─┼─▶ hash(key) ───┼─ queue ─▶ writer ─▶ shard-1.db
client ─┘                └─ ...
```

[`blobstore.py`](blobstore.py) is the store: you don't need to edit it. Every commit is
fsynced (`synchronous=FULL`), like durable storage. [`config.py`](config.py) is the one
file you change:

| Setting | Meaning |
|---|---|
| `SHARDS` | how many SQLite files, each with its own writer |
| `BATCH_SIZE` | how many queued writes a writer commits at once |
| `ASYNC_ACK` | `True` acknowledges a write as soon as it's queued in memory |

## 1. Hit the wall

```bash
python3 lab.py wall
```

16 clients write 8 KB blobs for 4 seconds through one file and one writer. Every
write waits for its own fsync, so throughput is a few hundred writes a second.

## 2. Shard and batch

Raise `SHARDS` and `BATCH_SIZE`, then run `wall` again. Batching lets one fsync cover
many writes; shards let several writers commit at once.

## 3. The fast mode, and what it costs

Set `ASYNC_ACK = True` and run:

```bash
python3 lab.py crash
```

It writes from a separate process, reads every acknowledgement, then `kill -9`s it
mid-burst and reopens the files. Example from a test run:

```
acknowledged 5,149, lost after kill -9: 4,096
```

Every one of those 4,096 writes was acknowledged to the client and is gone. That's
the trade Blobasaur's async mode makes: fine for chart layouts, not for trades.

## 4. Check it

```bash
python3 lab.py check
```

Passes when your config is at least **4x** faster than one shard with batch size 1
**and** loses **zero** acknowledged writes in the crash test. So the fast mode won't
pass: you have to get the speed from sharding and batching.

```
baseline (1 shard, batch 1): 458 writes/s
your config:                 7,231 writes/s  (15.8x)
crash test: acknowledged 916, lost 0
PASS: at least 4x faster, and no acknowledged write was lost
```

A sample answer is in [`solution/config.py`](solution/config.py). Try it yourself first.

## Stretch

1. Find the point where more shards stop helping on your machine. What's the bottleneck now?
2. Add a `delete()` to `blobstore.py` that goes through the queue, then make `get()`
   return the old value right after a delete in async mode. Fix it the way Zerodha did:
   check pending writes, including tombstones, before reading the file.

## Run the lab's tests

```bash
bash ci.sh
```

## Further reading

- [Zerodha Tech: Distributed, high-performance blob storage on SQLite](https://zerodha.tech/blog/high-performance-distributed-blob-storage/)
- [Blobasaur issue #35](https://github.com/iamd3vil/blobasaur/issues/35) and [the fix in PR #36](https://github.com/iamd3vil/blobasaur/pull/36): a cluster write accepted and then lost after a node came back
