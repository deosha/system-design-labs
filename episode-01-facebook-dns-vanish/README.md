# Episode 1 lab: the day Facebook vanished

[![labs](https://github.com/deosha/system-design-labs/actions/workflows/labs.yml/badge.svg)](https://github.com/deosha/system-design-labs/actions/workflows/labs.yml)

On 4 October 2021, Meta's DNS servers were still running, but every DNS site withdrew
its route at the same moment, so nobody could look up facebook.com. Each site was
following a sensible rule: *if I can't reach the data centres, step aside.* The
backbone was broken everywhere, so every site stepped aside together.

In this lab you reproduce that on your laptop, change one decision, and prove the fix.

**Time:** about 20 minutes · **Needs:** Python 3.10+, `dnslib` · **Runs on:** `127.0.0.1` only

## The setup

```
           backbone (HTTP on :8053)
                 ▲          ▲
   health check  │          │  health check
          ┌──────┴──┐   ┌───┴─────┐
          │ site-a  │   │ site-b  │    authoritative DNS for shop.example
          │  :5301  │   │  :5302  │    → 10.0.2.10
          └─────────┘   └─────────┘
```

Each site checks the backbone. `policy.should_answer()` decides whether the site keeps
its route (keeps answering) or withdraws.

## 1. Watch it break

```bash
pip install -r requirements.txt
python3 vanish.py withdraw
```

```
[backbone up]   shop.example -> 10.0.2.10 (answered by site-a)
                site-a: process running, answering, site-b: process running, answering
... maintenance command: backbone disconnected
[backbone down] shop.example -> NO ANSWER from any DNS server
                site-a: process running, withdrawn, site-b: process running, withdrawn
```

Both processes are still running. The shop has vanished anyway.

## 2. Fix it

Edit `should_answer(name, healthy, can_answer, sites)` in [`policy.py`](policy.py).

| Argument | Meaning |
|---|---|
| `healthy` | can this site reach the data centres over the backbone? |
| `can_answer` | the site's self-test: does it still hold a valid answer for `shop.example`? |
| `sites` | every site's state, if you want to look at the others |

Goal: **fail static.** Keep the last working route while the site can still answer correctly.

## 3. Check it

```bash
python3 vanish.py check
```

The starter fails with `FAIL: shop.example vanished` (exit code 1). A correct fix ends with:

```
PASS: shop.example still resolves with the backbone down
```

A sample fix is in [`solution/policy.py`](solution/policy.py). Try it yourself first.

## Stretch

Failing static has its own risk. A site that can no longer answer correctly should still
step aside. Break one site's record so `can_answer` is false, then confirm that only
that site withdraws while the other keeps the shop reachable.

## Run the lab's tests

```bash
bash ci.sh
```

This is the same script CI runs. It checks that the outage reproduces, that the starter
fails, and that the solution passes.

## Further reading

- [Meta Engineering: More details about the October 4 outage](https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/)
