from botmoduleproject1.modules.pm6_post_trade.intake.normalizer import NormalizedObserve, normalize
from botmoduleproject1.modules.pm6_post_trade.intake.validators import validate_observe


class PostTradeIntakeGateway:
    def validate(self, execution, risk, *, now, config, feature_enabled):
        return validate_observe(
            execution, risk, now=now, config=config, feature_enabled=feature_enabled
        )

    def normalize(self, execution, risk, now) -> NormalizedObserve:
        return normalize(execution, risk, now)
