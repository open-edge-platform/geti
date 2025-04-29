import logging
import os

logger = logging.getLogger(__name__)


def kafka_bootstrap_endpoints() -> str:
    """
    Returns the Kafka endpoints based on configured environment variables
    """
    return os.getenv("KAFKA_ADDRESS", "localhost:9092")


def kafka_security_enabled() -> bool:
    """
    Checks if kafka security is enabled
    """
    username = kafka_username()
    return len(username.strip()) > 0


def kafka_username() -> str:
    """
    Returns the Kafka username based on configured environment variables
    """
    default_kafka_username = ""
    return os.environ.get("KAFKA_USERNAME", default_kafka_username)


def kafka_password() -> str:
    """
    Returns the Kafka password based on configured environment variables
    """
    default_kafka_password = ""
    return os.environ.get("KAFKA_PASSWORD", default_kafka_password)


def kafka_security_protocol() -> str:
    """
    Returns the Kafka security protocol based on configured environment variable
    """
    default_kafka_security_protocol = "SASL_PLAINTEXT"
    return os.environ.get("KAFKA_SECURITY_PROTOCOL", default_kafka_security_protocol)


def kafka_sasl_mechanism() -> str:
    """
    Returns the Kafka sasl mechanism based on configured environment variable
    """
    default_kafka_sasl_mechanism = "SCRAM-SHA-512"
    return os.environ.get("KAFKA_SASL_MECHANISM", default_kafka_sasl_mechanism)


def kafka_topic_prefix() -> str:
    """
    Returns the Kafka topics prefix
    """
    default_kafka_topic_prefix = ""
    return os.environ.get("KAFKA_TOPIC_PREFIX", default_kafka_topic_prefix)
