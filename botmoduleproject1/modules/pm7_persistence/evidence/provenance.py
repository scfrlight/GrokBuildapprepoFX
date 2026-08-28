from botmoduleproject1.contracts.v1.persistence import PersistenceTruthSource


def disclose(truth: PersistenceTruthSource) -> str:
    return truth.value
