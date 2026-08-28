from botmoduleproject1.contracts.v1.post_trade import OperationalTruthBundle


class PublicationGateway:
    def publish(self, bundle: OperationalTruthBundle) -> OperationalTruthBundle:
        return bundle
