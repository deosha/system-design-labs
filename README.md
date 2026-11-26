# System Design Labs

[![labs](https://github.com/deosha/system-design-labs/actions/workflows/labs.yml/badge.svg)](https://github.com/deosha/system-design-labs/actions/workflows/labs.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

Hands-on labs for **System Design for DevOps & Cloud Engineers**, the video series on the
By Induction YouTube channel.

Every episode starts with a real outage. Each lab lets you reproduce the failure on your
laptop, change one design decision, and prove the fix with a checker.

## Labs

| Ep | Lab | You break | You fix | Concepts |
|---|---|---|---|---|
| 1 | [The day Facebook vanished](episode-01-facebook-dns-vanish/) | Two healthy DNS sites withdraw themselves and the shop disappears | Fail static: keep the last working route while a site can still answer | DNS, health checks, fail static, correlated failure |
| 2 | [Zerodha's storage hit a wall](episode-02-zerodha-blob-store/) | One SQLite writer caps throughput; async acks lose writes on kill -9 | Shards and batched commits, at least 4x faster with zero lost writes | sharding, group commit, durability trade-offs |

Each lab is standalone. Pick any folder and do them in any order.

## Quick start

```bash
git clone https://github.com/deosha/system-design-labs.git
cd system-design-labs/episode-01-facebook-dns-vanish
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 vanish.py withdraw    # watch it break
python3 vanish.py check       # FAIL until you fix policy.py
```

Everything runs locally on `127.0.0.1`. No cloud account, Docker or root needed.

## Repository layout

```
episode-NN-<name>/
  README.md          what happened, what to do, how to check
  requirements.txt   the lab's Python dependencies
  <lab>.py           the simulation (you don't need to edit it)
  policy.py / config.py   the one file you change
  solution/          a sample fix (try first, peek later)
  ci.sh              the lab's own test, run by CI
```

## Continuous integration

[`.github/workflows/labs.yml`](.github/workflows/labs.yml) finds every `episode-*` folder and
runs its `ci.sh` on Python 3.10, 3.12 and 3.13, on every push and pull request. For each lab, CI checks that:

1. the outage reproduces with the starter code,
2. the starter `policy.py` **fails** the checker, so the exercise isn't already solved,
3. `solution/policy.py` **passes** it.

Run the same check locally:

```bash
bash episode-01-facebook-dns-vanish/ci.sh
```

## Contributing

Found a bug or have a better fix? Open an issue or a pull request. Keep each lab
self-contained, runnable offline, and covered by its own `ci.sh`.

## License

[MIT](LICENSE)
