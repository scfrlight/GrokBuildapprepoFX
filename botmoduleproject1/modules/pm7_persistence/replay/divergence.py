def compare_snapshot(reconstructed: dict, snapshot_payload: dict) -> list[str]:
    notes = []
    expected = snapshot_payload.get("journal_sequence")
    actual = reconstructed.get("journal_sequence")
    if expected is not None and actual is not None and expected != actual:
        notes.append(f"sequence divergence expected={expected} actual={actual}")
    expected_hash = snapshot_payload.get("checksum")
    actual_hash = reconstructed.get("checksum")
    if expected_hash and actual_hash and expected_hash != actual_hash:
        notes.append("checksum divergence")
    return notes
