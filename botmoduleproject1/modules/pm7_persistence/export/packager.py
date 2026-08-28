from botmoduleproject1.contracts.v1.persistence import ExportPackage, IntegrityState, PersistenceTruthSource
from botmoduleproject1.modules.pm7_persistence.export.formats import to_markdown
from botmoduleproject1.modules.pm7_persistence.export.manifests import export_manifest
from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex


class ExportService:
    def pack(self, *, now, kind: str, records, integrity: IntegrityState, truth: PersistenceTruthSource) -> ExportPackage:
        ids = tuple(str(r.event.event_id) for r in records)
        payload = {
            "kind": kind,
            "event_ids": list(ids),
            "count": len(records),
            "truth_source": truth.value,
            "integrity": integrity.value,
        }
        checksum = sha256_hex(payload)
        manifest = export_manifest(kind=kind, event_ids=ids, checksum=checksum, integrity=integrity.value)
        return ExportPackage(
            occurred_at=now,
            kind=kind,
            json_payload=payload,
            markdown=to_markdown(payload),
            manifest=manifest,
            checksum=checksum,
            lineage_refs=ids,
            integrity_status=integrity,
            truth_source=truth,
        )
