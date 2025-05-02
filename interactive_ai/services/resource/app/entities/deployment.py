# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import abc
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from geti_types import ID
from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.utils.time_utils import now


@dataclass
class ModelIdentifier:
    """
    Model Identifier to identify models
    """

    model_storage_id: ID
    model_id: ID


class DeploymentState(Enum):
    """
    Enum representing state of Deployment
    """

    NONE = 0
    PREPARING = 1
    DONE = 2
    FAILED = 3


class Deployment(PersistentEntity, metaclass=abc.ABCMeta):
    """
    Deployment state of project level export
    Initializes a Deployment object.

    :param creator_id: ID of the person who started the deployment.
    :param id_: The ID of the Deployment object.
    :param progress: float that indicates the progress of the deployment
    :param state: enum representing the deployment state
    :param message: string containing the message from the deployment process
    :creation_time: date representing when the deployment has been created.
    :param ephemeral: True if the Deployment instance exists only in
       memory, False if it is backed up by the database
    """

    def __init__(
        self,
        id_: ID,
        creator_id: str,
        progress: float = 0,
        state: DeploymentState = DeploymentState.NONE,
        message: str = "",
        creation_time: datetime | None = None,
        ephemeral: bool = False,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.progress = progress
        self.state = state
        self.creation_time = now() if creation_time is None else creation_time
        self.creator_id = creator_id
        self.message = message


@dataclass
class CodeDeployment(Deployment):
    """
    Deployment state of code level export.

    The code deployment entity solves the problem of being only able to export one model
    at a time. With this entity you can export a whole project,
    including all the models in the task chain.
    All the models in the project will have a folder with files to run the model on your
    local machine and will be exported to a zip file which will be saved
    to the binary repo. The exporting will happen asynchronously, so a
    state and progress variable is needed to keep track of the deployment.


    :param creator_id: ID of the person who started the deployment.
    :param id_: The ID of the Code Deployment object.
    :param progress: float that indicates the progress of the deployment
    :param state: enum representing the deployment state
    :param message: string containing the message from the deployment process
    :param model_identifiers: List of ModelIdentifier objects
    :param binary_filename: string that represents the filename of where the deployed code is saved
    :creation_time: date representing when the deployment has been created.
    :param ephemeral: True if the CodeDeployment instance exists only in
       memory, False if it is backed up by the database
    """

    def __init__(  # noqa: PLR0913
        self,
        id_: ID,
        creator_id: str,
        progress: float = 0,
        state: DeploymentState = DeploymentState.NONE,
        message: str = "",
        model_identifiers: list[ModelIdentifier] | None = None,
        binary_filename: str | None = None,
        creation_time: datetime | None = None,
        ephemeral: bool = False,
    ) -> None:
        super().__init__(
            id_=id_,
            creator_id=creator_id,
            progress=progress,
            state=state,
            message=message,
            creation_time=creation_time,
            ephemeral=ephemeral,
        )
        self.model_identifiers = model_identifiers if model_identifiers else []
        self.binary_filename = binary_filename

    def __eq__(self, other: object):
        if not isinstance(other, CodeDeployment):
            return False
        return (
            self.creator_id == other.creator_id
            and self.id_ == other.id_
            and self.progress == other.progress
            and self.state == other.state
            and self.model_identifiers == other.model_identifiers
            and self.message == other.message,
        )


class NullCodeDeployment(CodeDeployment):
    """Representation of a 'CodeDeployment' not found'"""

    def __init__(self) -> None:
        super().__init__(creator_id="", id_=ID())
