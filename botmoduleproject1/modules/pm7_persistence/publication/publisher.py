from botmoduleproject1.contracts.v1.persistence import PersistencePublicationBundle
from botmoduleproject1.modules.pm7_persistence.publication.downstream_mapping import handoff


class PublicationService:
    def __init__(self) -> None:
        self.emitted = []

    def publish(self, bundle: PersistencePublicationBundle) -> PersistencePublicationBundle:
        # Downstream offline is fine: keep an in-process copy.
        assert bundle.persistence_handoff == handoff()
        self.emitted.append(bundle)
        return bundle
