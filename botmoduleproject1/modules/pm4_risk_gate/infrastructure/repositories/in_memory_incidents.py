from botmoduleproject1.modules.pm4_risk_gate.governance.incidents import IncidentLog


class InMemoryIncidentRepository(IncidentLog):
    uri = "memory://pm4-incidents"
