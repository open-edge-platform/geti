# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING

from dependencies import get_session
from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_logger_tools.logger_config import initialize_logger
from kafka_events.message import MeteringEvent, ResourceConsumption
from service.transaction import TransactionService
from utils.enums import ExternalServiceName, map_service_name

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = initialize_logger(__name__)


class KafkaHandler(BaseKafkaHandler):
    """
    Class handling credit-system related Kafka events
    """

    def __init__(self) -> None:
        super().__init__(group_id="credit_system_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="credits_lease", callback=self.process_lease),
        ]

    def process_lease(self, raw_message: KafkaRawMessage) -> None:
        """
        Credits lease is processed basing on received number of consumed credits and the mode.
        The "mode" header specifies how lease credits are consumed. When set to "chunked," lease credits are consumed
        through multiple operations.
        When set to "one-off" (default), the lease credits are consumed entirely in a single operation,
        and the lease can be closed once such metering event is received.
        """
        value: dict = raw_message.value
        headers = {key: value_bytes.decode("utf-8") for key, value_bytes in raw_message.headers}
        logger.info(f"Received metering event with {headers=} and message: {value}")

        mode = headers.get("mode", "one-off")
        organization_id = headers.get("organization_id")

        service_name = value.get("service_name", "")
        if not ExternalServiceName.contains(service_name):
            logger.error(f"Received unsupported service name: {service_name}")
        else:
            service_name = map_service_name(external_value=service_name)

        consumption: list = value.get("consumption", [])
        if not consumption:
            logger.error("Metering event has to contain at least one consumption record.")
            return

        res_consumption: list[ResourceConsumption] = [
            ResourceConsumption(unit=res.get("unit"), amount=res.get("amount")) for res in consumption
        ]

        msg = MeteringEvent(
            service_name=service_name,
            project_id=value.get("project_id"),
            workspace_id=headers.get("workspace_id"),
            lease_id=value.get("lease_id", ""),
            consumption=res_consumption,
            date=value.get("date"),
        )

        if mode == "one-off":  # other option - "chunked" mode - is to be implemented in the later release
            logger.info(
                f"Starting the process of {msg.lease_id} lease finalization, project id: {msg.project_id}, "
                f"consumed resources: {msg.consumption}."
            )
            db_session: Session = next(get_session())
            lease_svc = TransactionService(db_session)
            lease_svc.finalize_lease(
                metering_data=msg,
                organization_id=organization_id,
                _db_session=db_session,
            )
