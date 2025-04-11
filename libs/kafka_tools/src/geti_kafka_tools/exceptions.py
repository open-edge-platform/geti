class TopicAlreadySubscribedException(RuntimeError):
    """
    Raised when one attempts to subscribe to the same topic twice from an event consumer
    """

    def __init__(self, topic: str) -> None:
        super().__init__(f"Cannot subscribe to topic `{topic}` twice from the same consumer")


class TopicNotSubscribedException(RuntimeError):
    """
    Raised when one attempts to unsubscribe from a topic without having previously
    subscribed to it.
    """

    def __init__(self, topic: str) -> None:
        super().__init__(f"Consumer cannot unsubscribe from non-subscribed topic `{topic}`.")
