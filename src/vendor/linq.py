"""
LINQ-style collection operations for Yurilang
Loaded via `bin/` DLL convention — no external deps
"""

def linq_filter(collection, predicate):
    return [x for x in collection if predicate(x)]

def linq_weave(collection, transform):
    return [transform(x) for x in collection]

def linq_firstlove(collection, predicate=None):
    for x in collection:
        if predicate is None or predicate(x):
            return x
    return None

def linq_yearn(collection, predicate):
    return any(predicate(x) for x in collection)

def linq_vow(collection, predicate):
    return all(predicate(x) for x in collection)

def linq_tally(collection, predicate=None):
    if predicate:
        return sum(1 for x in collection if predicate(x))
    return len(collection)

def linq_rank(collection, key=None):
    return sorted(collection, key=key)

def linq_rankdown(collection, key=None):
    return sorted(collection, key=key, reverse=True)

def linq_ignore(collection, n):
    return collection[n:]

def linq_cherish(collection, n):
    return collection[:n]

def linq_pour(collection):
    return sum(collection)

def linq_spiral(collection, func, initial=None):
    from functools import reduce
    if initial is not None:
        return reduce(func, collection, initial)
    return reduce(func, collection)

def linq_cluster(collection, key):
    groups = {}
    for x in collection:
        k = key(x)
        groups.setdefault(k, []).append(x)
    return groups

LINQ_OPS = {
    "filter":    linq_filter,
    "weave":     linq_weave,
    "firstlove": linq_firstlove,
    "yearn":     linq_yearn,
    "vow":       linq_vow,
    "tally":     linq_tally,
    "rank":      linq_rank,
    "rankdown":  linq_rankdown,
    "ignore":    linq_ignore,
    "cherish":   linq_cherish,
    "pour":      linq_pour,
    "spiral":    linq_spiral,
    "cluster":   linq_cluster,
}
