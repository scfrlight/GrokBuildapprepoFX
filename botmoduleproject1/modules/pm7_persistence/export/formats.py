def to_markdown(payload: dict) -> str:
    lines = ["# PM7 evidence export", ""]
    for key, value in payload.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)
