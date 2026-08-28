"""Bayesian upgrade path. Disabled identity. Not QRF/ML."""


class BayesianUpdatePolicy:
    enabled = False

    def update(self, prior: float, evidence: float) -> float:
        if not self.enabled:
            return prior
        p = min(1.0, max(1e-6, prior))
        e = min(1.0, max(1e-6, evidence))
        # Odds-form blend reserved for a later sequence.
        return min(1.0, max(0.0, 0.7 * p + 0.3 * e))
