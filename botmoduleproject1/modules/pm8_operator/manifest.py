from botmoduleproject1.modules.pm8_operator.capabilities import PM8_OPERATOR_METADATA


def module_manifest() -> dict:
    meta = PM8_OPERATOR_METADATA
    return {
        "name": meta.name,
        "version": meta.version,
        "role": "operator_control_hitl",
        "depends_on": list(meta.dependencies),
        "accepts": ["OperatorCommand", "TelegramInbound", "ApprovalRequest", "TuningChangeRequest"],
        "does_not": [
            "orders",
            "mt5",
            "bypass_pm4",
            "enable_live",
            "auto_rearm",
            "telegram_bot_api",
            "auto_promote_to_live",
            "broker_commands",
        ],
        "capabilities": [
            "command_intake",
            "rbac",
            "hitl_queue",
            "simulated_transport",
            "operator_views",
            "command_audit",
            "studio_proposals",
        ],
        "truth": "operator_command_only",
        "durable": False,
        "transport": "simulated",
        "execution_permitted": False,
    }
