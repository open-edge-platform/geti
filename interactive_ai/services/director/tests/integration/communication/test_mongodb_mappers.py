# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.


from tests.test_helpers import verify_mongo_mapper

from active_learning.entities import ActiveScore, ActiveSuggestion, TaskActiveScore
from active_learning.storage.mappers.mongodb import ActiveScoreToMongo, ActiveSuggestionToMongo
from entities.dataset_item_count import DatasetItemCount, LabelData
from entities.dataset_item_labels import DatasetItemLabels
from storage.mappers import DatasetItemCountToMongo, DatasetItemLabelsToMongo


class TestMongoMappers:
    def test_dataset_item_count_mapper(self, request, fxt_mongo_id, fxt_label) -> None:
        """
        <b>Description:</b>
        Checks that the DatasetItemCountToMongo properly maps
        to mongo and back.

        <b>Input data:</b>
        Dummy DatasetItemCount

        <b>Expected results:</b>
        Test passes if DatasetItemCount can be mapped to mongo and back

        <b>Steps</b>
        1. Create dummy DatasetItemCount
        2. Map the entity to mongo and back, and compare with the original
        3. Map the entity to mongo again, and compare the documents
        """
        entity = DatasetItemCount(
            task_node_id=fxt_mongo_id(0),
            task_label_data=[LabelData.from_label(fxt_label)],
            n_dataset_items=1,
            unassigned_dataset_items=[fxt_mongo_id(4)],
            n_items_per_label={fxt_label.id_: 10},
        )

        verify_mongo_mapper(entity_to_map=entity, mapper_class=DatasetItemCountToMongo)

    def test_dataset_item_labels_mapper(self, request, fxt_mongo_id, fxt_dataset_storage, fxt_label) -> None:
        """
        <b>Description:</b>
        Checks that the DatasetItemLabelsToMongo properly maps
        to mongo and back.

        <b>Input data:</b>
        Dummy DatasetItemLabels

        <b>Expected results:</b>
        Test passes if DatasetItemLabels can be mapped to mongo and back

        <b>Steps</b>
        1. Create dummy DatasetItemLabels
        2. Map the entity to mongo and back, and compare with the original
        3. Map the entity to mongo again, and compare the documents
        """
        entity = DatasetItemLabels(
            dataset_item_id=fxt_mongo_id(0),
            label_ids=[fxt_mongo_id(2)],
        )

        verify_mongo_mapper(entity_to_map=entity, mapper_class=DatasetItemLabelsToMongo)

    def test_active_score_mapper(self, fxt_ote_id, fxt_media_identifier) -> None:
        """
        <b>Description:</b>
        Check the MongoDB mapper for ActiveScore

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Test passes if ActiveScore can be mapped to and from MongoDB successfully.

        <b>Steps</b>
        1. Create a dummy ActiveScore
        2. Map the entity to mongo and back, and compare with the original
        3. Map the entity to mongo again, and compare the documents
        """
        task_score_1 = TaskActiveScore(
            model_id=fxt_ote_id(1),
            score=0.5,
            extractors_scores={"extr_1": 0.4, "extr_2": 0.5},
        )
        task_score_2 = TaskActiveScore(
            model_id=fxt_ote_id(2),
            score=0.9,
            extractors_scores={"extr_1": 0.9, "extr_2": 0.1},
        )
        score = ActiveScore(
            media_identifier=fxt_media_identifier,
            pipeline_score=0.7,
            tasks_scores={
                fxt_ote_id(3): task_score_1,
                fxt_ote_id(4): task_score_2,
            },
        )

        verify_mongo_mapper(entity_to_map=score, mapper_class=ActiveScoreToMongo)

    def test_active_suggestion_mapper(self, fxt_ote_id, fxt_media_identifier) -> None:
        """
        <b>Description:</b>
        Check the MongoDB mapper for ActiveSuggestion

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Test passes if ActiveSuggestion can be mapped to and from MongoDB successfully.

        <b>Steps</b>
        1. Create a dummy ActiveSuggestion
        2. Map the entity to mongo and back, and compare with the original
        3. Map the entity to mongo again, and compare the documents
        """
        suggestion = ActiveSuggestion(
            id_=fxt_ote_id(1),
            media_identifier=fxt_media_identifier,
            score=0.7,
            models=[fxt_ote_id(2), fxt_ote_id(3)],
            user="user",
            reason="reason",
        )

        verify_mongo_mapper(entity_to_map=suggestion, mapper_class=ActiveSuggestionToMongo)
