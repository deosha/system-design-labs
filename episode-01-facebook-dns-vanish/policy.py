"""Decide whether a DNS site keeps its route. This is the file you change in the lab.

healthy     -- can this site reach the data centres over the backbone?
can_answer  -- can this site still give a valid answer for shop.example?
sites       -- every site, if you want to look at the others (stretch goal)
"""
MODE = "withdraw"


def should_answer(name, healthy, can_answer, sites):
    if MODE == "withdraw":
        # The 2021 design: lose the backbone, withdraw the route. Sensible for one site alone.
        return healthy
    # Your fix goes here. Hint: the backbone check is true, but is it the right question?
    return healthy
