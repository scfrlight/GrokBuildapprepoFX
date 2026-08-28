from botmoduleproject1.contracts.v1.post_trade import ControlRequestKind, IncidentType

TYPE_TO_REQUEST = {
    IncidentType.KILL_STATE_BREACH: ControlRequestKind.FREEZE,
    IncidentType.UNEXPECTED_TRADING_CONTINUATION: ControlRequestKind.ORDERLY_WITHDRAWAL,
    IncidentType.ORDERLY_WITHDRAWAL_REQUIRED: ControlRequestKind.ORDERLY_WITHDRAWAL,
    IncidentType.RECONCILIATION_FOLLOWUP_REQUIRED: ControlRequestKind.NO_NEW_RISK,
    IncidentType.POST_TRADE_CONTROL_BREACH: ControlRequestKind.CLOSE_ONLY,
}
