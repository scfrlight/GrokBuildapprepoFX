def is_authorized(spec) -> bool:
    return bool(spec.authorized) and bool(spec.actor and spec.actor.strip())
