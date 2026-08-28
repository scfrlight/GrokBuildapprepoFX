from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import ExecutionPublicationBundle, ReconciliationOutcome
from botmoduleproject1.contracts.v1.post_trade import TruthSource


def classify_truth(bundle: ExecutionPublicationBundle | None) -> TruthSource:
    if bundle is None:
        return TruthSource.UNKNOWN
    recon = bundle.reconciliation
    if recon is not None and recon.outcome in {ReconciliationOutcome.MISMATCH, ReconciliationOutcome.CRITICAL}:
        return TruthSource.UNRESOLVED_MISMATCH
    ticket = bundle.order.broker_ticket if bundle.order else None
    if ticket and str(ticket).startswith("SIM-"):
        return TruthSource.SIMULATION_TRUTH
    if bundle.execution_mode.value == "simulation" or bundle.receipt.simulation:
        return TruthSource.SIMULATION_TRUTH
    if recon is not None and recon.broker_truth_available and recon.outcome.value == "pass":
        return TruthSource.RECONCILED_TRUTH
    if bundle.order is not None:
        return TruthSource.LOCAL_OMS_TRUTH
    return TruthSource.UNKNOWN


def approved_qty(bundle: ExecutionPublicationBundle) -> object:
    if bundle.command is not None:
        return bundle.command.approved_quantity
    if bundle.order is not None:
        return bundle.order.original_quantity
    return None


def filled_qty(bundle: ExecutionPublicationBundle):
    if bundle.order is not None:
        return bundle.order.filled_quantity
    total = None
    for fill in bundle.fills:
        total = fill.quantity if total is None else total + fill.quantity
    return total
