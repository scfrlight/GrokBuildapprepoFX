def honest_metrics(dataset) -> str:
    if dataset.quality.value == "insufficient_data":
        return "insufficient_data"
    return "lineage_aware"
