def format_line(kind: str, detail: str, when) -> str:
    return f"{when.isoformat()} {kind} {detail}"
