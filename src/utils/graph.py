def tuples_to_graph_nodes(
    tuples: list[tuple],
) -> list[dict]:
    return [
        {
            "id": str(t[0]),
            "name": t[1],
            "value": t[2],
            "category": t[3],
        }
        for t in tuples
    ]


def tuples_to_graph_links(
    tuples: list[tuple],
) -> list[dict]:
    return [
        {
            "source": str(t[0]),
            "target": str(t[1]),
            "weight": t[2],
        }
        for t in tuples
    ]
