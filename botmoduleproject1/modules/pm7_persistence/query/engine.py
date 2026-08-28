from botmoduleproject1.contracts.v1.persistence import QueryResult
from botmoduleproject1.modules.pm7_persistence.query.authorization import is_authorized
from botmoduleproject1.modules.pm7_persistence.query.filters import apply_filters


class QueryService:
    def execute(self, spec, records, *, limit_cap: int = 50) -> QueryResult:
        if not is_authorized(spec):
            return QueryResult(
                query_id=spec.query_id,
                authorized=False,
                parameters={"actor": spec.actor},
                access="rejected",
                reasons=("unauthorized",),
                limit=spec.limit,
                offset=spec.offset,
            )
        items = apply_filters(records, spec)
        limit = min(spec.limit, limit_cap)
        window = items[spec.offset : spec.offset + limit]
        return QueryResult(
            query_id=spec.query_id,
            authorized=True,
            parameters={"actor": spec.actor, "limit": limit, "offset": spec.offset},
            event_ids=tuple(str(r.event.event_id) for r in window),
            count=len(items),
            offset=spec.offset,
            limit=limit,
            provenance=tuple(r.event.truth_source.value for r in window),
            access="granted",
        )
