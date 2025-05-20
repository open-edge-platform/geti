#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for label related entities"""

from iai_core.entities.color import Color
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema, LabelSchemaView, LabelTree
from iai_core.entities.scored_label import LabelSource, ScoredLabel
from iai_core.repos.mappers.mongodb_mapper_interface import (
    IMapperForward,
    IMapperProjectIdentifierBackward,
    IMapperSimple,
)
from iai_core.utils.timed_lru_cache import timed_lru_cache

from .id_mapper import IDToMongo
from .primitive_mapper import DatetimeToMongo
from geti_types import ID, ProjectIdentifier


class ColorToMongo(IMapperSimple[Color, dict]):
    """MongoDB mapper for `Color` entities"""

    @staticmethod
    def forward(instance: Color) -> dict:
        return {
            "red": instance.red,
            "green": instance.green,
            "blue": instance.blue,
            "alpha": instance.alpha,
        }

    @staticmethod
    def backward(instance: dict) -> Color:
        return Color(instance["red"], instance["green"], instance["blue"], instance["alpha"])


class LabelToMongo(IMapperSimple[Label, dict]):
    """MongoDB mapper for `Label` entities"""

    @staticmethod
    def forward(instance: Label) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "name": instance.name,
            "color": ColorToMongo.forward(instance.color),
            "hotkey": instance.hotkey,
            "domain": str(instance.domain),
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "is_empty": instance.is_empty,
            "is_anomalous": instance.is_anomalous,
        }

    @staticmethod
    def backward(instance: dict) -> Label:
        label_id = IDToMongo.backward(instance["_id"])

        domain = instance.get("domain")
        label_domain = Domain[domain]  # type: ignore

        return Label(
            name=instance["name"],
            domain=label_domain,
            color=ColorToMongo.backward(instance["color"]),
            hotkey=instance.get("hotkey", ""),
            creation_date=DatetimeToMongo.backward(instance.get("creation_date")),
            is_empty=instance.get("is_empty", False),
            id_=label_id,
            is_anomalous=instance.get("is_anomalous", False),
            ephemeral=False,
        )


class LabelGroupToMongo(IMapperForward[LabelGroup, dict], IMapperProjectIdentifierBackward[LabelGroup, dict]):
    """MongoDB mapper for `LabelGroup` entities"""

    @staticmethod
    def forward(instance: LabelGroup) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "name": instance.name,
            "label_ids": [IDToMongo.forward(label.id_) for label in instance.labels],
            "relation_type": instance.group_type.name,
        }

    @staticmethod
    def backward(instance: dict, project_identifier: ProjectIdentifier) -> LabelGroup:
        from iai_core.repos import LabelRepo

        label_repo = LabelRepo(project_identifier)
        label_ids = [IDToMongo.backward(label_id) for label_id in instance["label_ids"]]
        label_map = label_repo.get_by_ids(label_ids)
        return LabelGroup(
            id=IDToMongo.backward(instance["_id"]),
            name=instance["name"],
            group_type=LabelGroupType[instance["relation_type"]],
            labels=[label_map[label_id] for label_id in label_ids],
        )


class LabelTreeToMongo(IMapperForward[LabelTree, dict], IMapperProjectIdentifierBackward[LabelTree, dict]):
    """MongoDB mapper for `LabelTree` entities"""

    @staticmethod
    def forward(instance: LabelTree) -> dict:
        return {
            "type": instance.type,
            "directed": instance.directed,
            "nodes": [IDToMongo.forward(label.id_) for label in instance.nodes],
            "edges": [(IDToMongo.forward(edge[0].id_), IDToMongo.forward(edge[1].id_)) for edge in instance.edges],
        }

    @staticmethod
    def backward(instance: dict, project_identifier: ProjectIdentifier) -> LabelTree:
        from iai_core.repos import LabelRepo

        label_repo = LabelRepo(project_identifier)
        label_tree = LabelTree()
        label_ids = tuple([IDToMongo.backward(label_id) for label_id in instance["nodes"]])
        label_map = label_repo.get_by_ids(label_ids)
        for label_id in label_ids:
            label_tree.add_node(label_map[label_id])
        for edge in instance["edges"]:
            label_tree.add_edge(
                label_map[IDToMongo.backward(edge[0])],
                label_map[IDToMongo.backward(edge[1])],
            )
        return label_tree


class LabelSchemaToMongo(IMapperSimple[LabelSchema, dict]):
    """MongoDB mapper for `LabelSchema` entities"""

    @staticmethod
    def forward(instance: LabelSchema) -> dict:
        # This is the only place where deleted labels should be taken into account for
        # the groups in the label schema.
        label_groups = [LabelGroupToMongo.forward(group) for group in instance._groups]

        mongo_dict = {
            "_id": IDToMongo.forward(instance.id_),
            "label_tree": LabelTreeToMongo.forward(instance.label_tree),
            "label_groups": label_groups,
            "previous_schema_revision_id": IDToMongo.forward(instance.previous_schema_revision_id),
            "deleted_label_ids": [IDToMongo.forward(id_) for id_ in instance.deleted_label_ids],
        }
        if isinstance(instance, LabelSchemaView):
            mongo_dict["parent_schema_id"] = IDToMongo.forward(instance.parent_schema.id_)
            mongo_dict["task_node_id"] = IDToMongo.forward(instance.task_node_id)
            mongo_dict["label_schema_class"] = "label_schema_view"
        else:
            mongo_dict["label_schema_class"] = "label_schema"
        return mongo_dict

    @staticmethod
    def backward(instance: dict) -> LabelSchema | LabelSchemaView:
        id_ = IDToMongo.backward(instance["_id"])
        # note: 'workspace_id' and 'project_id' are in the document because the repo
        # is SessionBasedProjectRepo
        project_identifier = ProjectIdentifier(
            workspace_id=IDToMongo.backward(instance["workspace_id"]),
            project_id=IDToMongo.backward(instance["project_id"]),
        )
        label_tree = LabelTreeToMongo.backward(
            instance["label_tree"],
            project_identifier=project_identifier,
        )
        label_groups = [
            LabelGroupToMongo.backward(label_group, project_identifier=project_identifier)
            for label_group in instance["label_groups"]
        ]
        previous_schema_revision_id = IDToMongo.backward(instance.get("previous_schema_revision_id", ""))
        schema_class = instance.get("label_schema_class", "label_schema")
        deleted_label_ids = [IDToMongo.backward(id_) for id_ in instance.get("deleted_label_ids", [])]
        if schema_class == "label_schema_view":
            from iai_core.repos import LabelSchemaRepo

            label_schema = LabelSchemaRepo(project_identifier).get_by_id(
                IDToMongo.backward(instance["parent_schema_id"])
            )
            task_node_id = IDToMongo.backward(instance.get("task_node_id", ""))
            output = LabelSchemaView(
                id_=id_,
                label_schema=label_schema,
                label_tree=label_tree,
                label_groups=label_groups,
                previous_schema_revision_id=previous_schema_revision_id,
                task_node_id=task_node_id,
                deleted_label_ids=deleted_label_ids,
            )
        else:
            project_id = IDToMongo.backward(instance.get("project_id", ""))
            output = LabelSchema(  # type: ignore
                id_=id_,
                label_tree=label_tree,
                label_groups=label_groups,
                previous_schema_revision_id=previous_schema_revision_id,
                project_id=project_id,
                deleted_label_ids=deleted_label_ids,
                ephemeral=False,
            )
        return output


class ScoredLabelToMongo(
    IMapperForward[ScoredLabel, dict],
    IMapperProjectIdentifierBackward[ScoredLabel, dict],
):
    """MongoDB mapper for `ScoredLabel` entities"""

    @staticmethod
    def forward(instance: ScoredLabel) -> dict:
        return {
            "label_id": IDToMongo.forward(instance.id_),
            "is_empty": instance.is_empty,
            "probability": instance.probability,
            "label_source": LabelSourceToMongo.forward(instance.label_source),
        }

    @staticmethod
    def backward(instance: dict, project_identifier: ProjectIdentifier) -> ScoredLabel:
        label_id = IDToMongo.backward(instance["label_id"])
        is_empty = instance.get("is_empty")

        if is_empty is None:
            label = ScoredLabelToMongo.get_label_by_id(label_id=label_id, project_identifier=project_identifier)
            is_empty = label.is_empty

        label_source_dict = instance.get("label_source")
        label_source = (
            LabelSourceToMongo.backward(label_source_dict) if label_source_dict is not None else LabelSource()
        )

        return ScoredLabel(
            label_id=label_id,
            is_empty=is_empty,
            probability=instance["probability"],
            label_source=label_source,
        )

    @staticmethod
    @timed_lru_cache(seconds=5)
    def get_label_by_id(label_id: ID, project_identifier: ProjectIdentifier) -> Label:
        """
        Method with short-lived cache to get label. This helps with performance of mapping annotations with multiple
        shapes with the same labels. Should be removed again once CVS-135291 is implemented.
        """
        from iai_core.repos import LabelRepo

        return LabelRepo(project_identifier).get_by_id(label_id)


class LabelSourceToMongo(IMapperSimple[LabelSource, dict]):
    """MongoDB mapper for `LabelSource` entities"""

    @staticmethod
    def forward(instance: LabelSource) -> dict:
        return {
            "user_id": instance.user_id,
            "model_id": IDToMongo.forward(instance.model_id),
            "model_storage_id": IDToMongo.forward(instance.model_storage_id),
        }

    @staticmethod
    def backward(instance: dict) -> LabelSource:
        user_id = instance["user_id"]
        model_id = IDToMongo.backward(instance["model_id"])
        model_storage_id = IDToMongo.backward(instance["model_storage_id"])

        return LabelSource(user_id=user_id, model_id=model_id, model_storage_id=model_storage_id)
