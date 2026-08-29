from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.operator import (
    CommandDisposition,
    HaltState,
    OperatorPublicationBundle,
    TransportMode,
)


class PublicationService:
    def publish(
        self,
        *,
        as_of: datetime,
        halt_state: HaltState,
        hitl_pending: int,
        studio_open: int,
        last_disposition: CommandDisposition | None,
        diagnostics: dict | None = None,
    ) -> OperatorPublicationBundle:
        return OperatorPublicationBundle(
            as_of=as_of,
            transport_mode=TransportMode.SIMULATED,
            halt_state=halt_state,
            hitl_pending=hitl_pending,
            studio_open=studio_open,
            last_disposition=last_disposition,
            diagnostics=diagnostics or {},
        )
