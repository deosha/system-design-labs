"""Sample solution: fail static.
Keep the last working route while the site can still answer correctly.
The backbone check is true, but it doesn't measure whether this site can do its own job."""
MODE = "failstatic"


def should_answer(name, healthy, can_answer, sites):
    if MODE == "withdraw":
        return healthy
    return healthy or can_answer
