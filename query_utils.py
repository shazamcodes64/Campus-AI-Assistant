def expand_query(query: str) -> str:
    """
    Simple rule-based expansion.
    Cheap but boosts recall massively.
    """

    expansions = {
        "placement": "placement recruitment hiring campus job selection interview process policy",
        "syllabus": "curriculum course structure subjects regulations credits",
        "policy": "rules guidelines regulation handbook process criteria"
    }

    words = query.lower().split()

    extra = []
    for w in words:
        if w in expansions:
            extra.append(expansions[w])

    return query + " " + " ".join(extra)
