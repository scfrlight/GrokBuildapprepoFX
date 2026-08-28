from botmoduleproject1.modules.pm4_risk_gate.governance.inventory import GovernanceRegistry


class InMemoryInventoryRepository(GovernanceRegistry):
    uri = "memory://pm4-inventory"
