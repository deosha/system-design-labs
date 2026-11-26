"""The one file you change in this lab."""

SHARDS = 1        # how many SQLite files (each has its own writer)
BATCH_SIZE = 1    # how many writes each writer commits at once
ASYNC_ACK = False # True: acknowledge a write as soon as it's queued in memory
