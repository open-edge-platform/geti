# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
from operator import attrgetter

import pytest
from testfixtures import compare

from active_learning.entities import ActiveScore, ActiveScoreSuggestionInfo, NullActiveScore
from active_learning.storage.repos.active_score_repo import ActiveScoreRepo

from geti_types import ID, DatasetStorageIdentifier, VideoFrameIdentifier, VideoIdentifier


class TestActiveScoreRepo:
    def test_save_and_load(self, request, fxt_project, fxt_dataset_storage, fxt_active_score_factory) -> None:
        """
        <b>Description:</b>
        Check that ActiveScoreRepo can save and retrieve ActiveScore items.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        The ActiveScore entities can be saved to the database and pulled from it.
        No two active scores relative to the same media are present at the same time.

        <b>Steps</b>
        1. Create an active score S1
        2. Save S1
        3. Load S1 from the repo and verify that it matches the original object
        4. Create an active score S2
        5. Save S2
        6. Reload both S1 and S2 and verify that they match the original objects
        7. Create an active score S3 with the same media identifier of S1
        8. Save S3
        9. Reload S1, S2 and S3 and verify that only S2 and S3 exist, while S1
           was overwritten by S3 because of the same media.
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        score_1 = fxt_active_score_factory(1, score=0.1)
        assert score_1.ephemeral
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save(score_1)
        assert not score_1.ephemeral
        score_1_reloaded = repo.get_by_id(score_1.id_)
        compare(score_1_reloaded, score_1, ignore_eq=True)

        repo.save(score_1_reloaded)
        score_1_reloaded_again = repo.get_by_id(score_1.id_)
        compare(score_1_reloaded_again, score_1, ignore_eq=True)

        score_2 = fxt_active_score_factory(2, score=0.2)
        repo.save(score_2)
        score_1_reloaded = repo.get_by_id(score_1.id_)
        score_2_reloaded = repo.get_by_id(score_2.id_)
        compare(score_1_reloaded, score_1, ignore_eq=True)
        compare(score_2_reloaded, score_2, ignore_eq=True)

        score_3 = fxt_active_score_factory(3, score=0.3, media_identifier=score_1.media_identifier)
        repo.save(score_3)
        score_1_reloaded = repo.get_by_id(score_1.id_)
        score_3_reloaded = repo.get_by_id(score_3.id_)
        compare(score_3_reloaded, score_3)
        compare(score_1_reloaded, score_3_reloaded)  # because 1 was overwritten by 3

    def test_save_many(self, request, fxt_project, fxt_dataset_storage, fxt_active_score_factory) -> None:
        """
        <b>Description:</b>
        Check that ActiveScoreRepo can save many ActiveScore items at once.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        The ActiveScore entities can be saved to the database and pulled from it.

        <b>Steps</b>
        1. Create two active scores
        2. Save them with method `save_many`
        3. Reload the scores and verify that they match the original objects
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        score_1 = fxt_active_score_factory(1)
        score_2 = fxt_active_score_factory(2)
        scores = (score_1, score_2)
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save_many(scores)

        score_1_reloaded = repo.get_by_id(score_1.id_)
        score_2_reloaded = repo.get_by_id(score_2.id_)
        compare(score_1_reloaded, score_1, ignore_eq=True)
        compare(score_2_reloaded, score_2, ignore_eq=True)

    def test_get_by_id(
        self,
        request,
        fxt_ote_id,
        fxt_project,
        fxt_dataset_storage,
        fxt_active_score_factory,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.get_by_id.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.get_by_id can retrieve the right item if it exists.

        <b>Steps</b>
        1. Create and save two active scores
        2. Call `get_by_id` to reload the first score
        3. Check that the returned object matches the original one
        4. Call `get_by_id` to load a non-existing object
        5. Check that no actual score is returned
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        scores = [fxt_active_score_factory(i) for i in range(2)]
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save_many(scores)

        first_score_reloaded = repo.get_by_id(scores[0].id_)
        compare(first_score_reloaded, scores[0], ignore_eq=True)

        non_exist_score = repo.get_by_id(fxt_ote_id(123456789))
        assert isinstance(non_exist_score, NullActiveScore)

    def test_get_by_media_identifier(
        self,
        request,
        fxt_project,
        fxt_dataset_storage,
        fxt_active_score_factory,
        fxt_media_identifier_factory,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.get_by_media_identifier.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.get_by_media_identifier can retrieve the right item if it exists.

        <b>Steps</b>
        1. Create and save two active scores
        2. Call `get_by_media_identifier` to reload the first score
        3. Check that the returned object matches the original one
        4. Call `get_by_media_identifier` to load a non-existing object
        5. Check that no actual score is returned
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        scores = [fxt_active_score_factory(i) for i in range(2)]
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save_many(scores)

        first_score_reloaded = repo.get_by_media_identifier(scores[0].media_identifier)
        compare(first_score_reloaded, scores[0], ignore_eq=True)

        non_exist_score = repo.get_by_media_identifier(fxt_media_identifier_factory(123456789))
        assert isinstance(non_exist_score, NullActiveScore)

    def test_get_by_media_identifiers(
        self,
        request,
        fxt_project,
        fxt_dataset_storage,
        fxt_active_score_factory,
        fxt_media_identifier_factory,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.get_by_media_identifiers.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.get_by_media_identifiers can retrieve the right items if they exists.

        <b>Steps</b>
        1. Create and save three active scores
        2. Call `get_by_media_identifiers` with the media identifiers of the first two
           scores and a non-existing media identifier.
        3. Verify that two scores are returned, and they correspond to the first two.
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        scores = [fxt_active_score_factory(i) for i in range(3)]
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save_many(scores)

        query_media_identifiers = [
            scores[0].media_identifier,
            scores[1].media_identifier,
            fxt_media_identifier_factory(123456789),
        ]
        scores_loaded = repo.get_by_media_identifiers(query_media_identifiers)

        assert len(scores_loaded) == 2
        assert set(scores_loaded) == {
            scores[0].media_identifier,
            scores[1].media_identifier,
        }
        compare(scores_loaded[scores[0].media_identifier], scores[0])
        compare(scores_loaded[scores[1].media_identifier], scores[1])

    def test_get_all(self, request, fxt_project, fxt_dataset_storage, fxt_active_score_factory) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.get_all.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.get_all pulls all the items.

        <b>Steps</b>
        1. Create and save two active scores
        2. Call `get_all`
        3. Check that all the items are returned
        """
        scores = [fxt_active_score_factory(i) for i in range(2)]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save_many(scores)

        scores_reloaded = list(repo.get_all())

        assert len(scores_reloaded) == 2
        scores_reloaded_sorted = sorted(scores_reloaded, key=attrgetter("id_"))
        compare(scores_reloaded_sorted, scores, ignore_eq=True)

    def test_delete_by_media_identifier(
        self,
        request,
        fxt_project,
        fxt_dataset_storage,
        fxt_active_score_factory,
        fxt_ote_id,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.delete_by_media_identifier.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.delete_by_media_identifier deletes the specified item.

        <b>Steps</b>
        1. Create and save two active scores
        2. Call `delete_by_media_identifier` on the first one.
        3. Check that the first score is no longer available in the database,
           while the second one is.
        4. Create and save two active scores for video frames
        5. Call `delete_by_media_identifier` on the video identifier
        6. Check that both frames scores get deleted
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        score_1 = fxt_active_score_factory(1)
        score_2 = fxt_active_score_factory(2)
        scores = [score_1, score_2]
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save_many(scores)

        repo.delete_by_media_identifier(scores[0].media_identifier)

        score_1_reloaded = repo.get_by_id(score_1.id_)
        score_2_reloaded = repo.get_by_id(score_2.id_)
        assert isinstance(score_1_reloaded, NullActiveScore)
        compare(score_2_reloaded, score_2, ignore_eq=True)

        frame_1_id = VideoFrameIdentifier(video_id=ID(fxt_ote_id(9)), frame_index=1)
        frame_2_id = VideoFrameIdentifier(video_id=ID(fxt_ote_id(9)), frame_index=2)
        video_id = VideoIdentifier(video_id=ID(fxt_ote_id(9)))
        score_3 = fxt_active_score_factory(3, media_identifier=frame_1_id)
        score_4 = fxt_active_score_factory(3, media_identifier=frame_2_id)
        repo.save_many([score_3, score_4])

        repo.delete_by_media_identifier(video_id)

        score_3_reloaded = repo.get_by_id(score_3.id_)
        score_4_reloaded = repo.get_by_id(score_4.id_)
        assert isinstance(score_3_reloaded, NullActiveScore)
        assert isinstance(score_4_reloaded, NullActiveScore)

    def test_delete_all(self, request, fxt_project, fxt_dataset_storage, fxt_active_score_factory) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.delete_all.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.delete_all deletes all the items.

        <b>Steps</b>
        1. Create and save two active scores
        2. Call `delete_all`
        3. Check that the scores are no longer available in the database
        """
        score_1 = fxt_active_score_factory(1)
        score_2 = fxt_active_score_factory(2)
        scores = [score_1, score_2]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save_many(scores)

        repo.delete_all()

        score_1_reloaded = repo.get_by_id(score_1.id_)
        score_2_reloaded = repo.get_by_id(score_2.id_)
        assert isinstance(score_1_reloaded, NullActiveScore)
        assert isinstance(score_2_reloaded, NullActiveScore)

    @pytest.mark.parametrize("mapped_only", [False, True], ids=["include unmapped", "exclude unmapped"])
    @pytest.mark.parametrize("consider_model", [False, True], ids=["ignore model", "consider model"])
    def test_find_best_candidates_project_level(
        self,
        request,
        mapped_only,
        consider_model,
        fxt_ote_id,
        fxt_project,
        fxt_dataset_storage,
        fxt_active_score_factory,
        fxt_media_identifier_factory,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.find_best_candidates on a project level.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.find_best_candidates returns the best scores
        for project-level active learning.

        <b>Steps</b>
        1. Create and save four active scores with custom project-level score values
           and other two scores with default values.
        2. Call 'find_best_candidates' to get the best set of 2 items.
           The input candidates are chosen so exclude the absolute best score.
        3. Verify that the output is well sorted and it contains the expected items
        4. Call 'find_best_candidates' to get the best set of 5 items.
        5. Verify that the output contains the right number of elements depending
           on whether the unmapped items are included or not in the query.
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        # fmt: off
        model_1_id, model_2_id, model_3_id = fxt_ote_id(101), fxt_ote_id(102), fxt_ote_id(103)
        score_0: ActiveScore = fxt_active_score_factory(index=0, score=0.7, model_ids=[model_1_id, model_2_id])
        score_1: ActiveScore = fxt_active_score_factory(index=1, score=0.3, model_ids=[model_1_id, model_2_id])
        score_2: ActiveScore = fxt_active_score_factory(index=2, score=0.1, model_ids=[model_1_id, model_2_id])
        score_3: ActiveScore = fxt_active_score_factory(index=3, score=0.5, model_ids=[model_2_id, model_3_id])
        # fmt: on
        score_4, score_5 = tuple(
            ActiveScore.make_default(
                id_=ActiveScoreRepo.generate_id(),
                media_identifier=fxt_media_identifier_factory(i),
                task_nodes_ids=[],
            )
            for i in (4, 5)
        )
        scores = [score_0, score_1, score_2, score_3, score_4, score_5]
        identifiers = [score.media_identifier for score in scores]
        repo.save_many(scores)
        candidates = [identifiers[0], identifiers[1], identifiers[3]]

        best_items = repo.find_best_candidates(
            candidate_media=candidates,
            size=2,
            inferred_only=mapped_only,
            models_ids=([model_1_id]) if consider_model else None,
        )

        if consider_model:
            # the output should contain score_1 and score_0 because score_2 is not
            # in the candidates list, while score_3 refers to another model.
            assert best_items == (
                ActiveScoreSuggestionInfo(
                    media_identifier=identifiers[1],
                    score=0.3,
                    models_ids=(model_1_id, model_2_id),
                ),
                ActiveScoreSuggestionInfo(
                    media_identifier=identifiers[0],
                    score=0.7,
                    models_ids=(model_1_id, model_2_id),
                ),
            )
        else:
            # the output should contain score_1 and score_3 because score_2 is not
            # in the candidates list; the model does not matter
            assert best_items == (
                ActiveScoreSuggestionInfo(
                    media_identifier=identifiers[1],
                    score=0.3,
                    models_ids=(model_1_id, model_2_id),
                ),
                ActiveScoreSuggestionInfo(
                    media_identifier=identifiers[3],
                    score=0.5,
                    models_ids=(model_2_id, model_3_id),
                ),
            )

        best_items = repo.find_best_candidates(
            candidate_media=identifiers,
            size=5,
            inferred_only=mapped_only,
            models_ids=([model_1_id]) if consider_model else None,
        )
        best_media_ids = {item.media_identifier for item in best_items}

        if mapped_only:
            # the output should contain all and only the 4 existing mapped scores
            # score_4 and score_5 are excluded because not-inferred.
            assert len(best_media_ids) == 4
            assert best_media_ids == set(identifiers[:4])
        else:
            # the output should contain the 4 existing mapped scores plus one between
            # score_4 and score_5. In total, 5 elements.
            assert len(best_media_ids) == 5
            assert set(identifiers[:4]).issubset(best_media_ids)

    @pytest.mark.parametrize("mapped_only", [False, True], ids=["include unmapped", "exclude unmapped"])
    @pytest.mark.parametrize("consider_model", [False, True], ids=["ignore model", "consider model"])
    def test_find_best_candidates_task_level(
        self,
        request,
        mapped_only,
        consider_model,
        fxt_ote_id,
        fxt_project,
        fxt_dataset_storage,
        fxt_active_score_factory,
        fxt_media_identifier_factory,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.find_best_candidates on a task level.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveScoreRepo.find_best_candidates returns the best scores
        for task-level active learning.

        <b>Steps</b>
        1. Create and save four active scores with custom task-level score values
           and other two scores with default values.
        2. Call 'find_best_candidates' to get the best set of 2 items.
           The input candidates are chosen so exclude the absolute best score.
        3. Verify that the output is well sorted and it contains the expected items
        4. Call 'find_best_candidates' to get the best set of 5 items.
        5. Verify that the output contains the right number of elements depending
           on whether the unmapped items are included or not in the query.
        """
        task_node_id = fxt_ote_id(1)
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        model_1_id, model_2_id = fxt_ote_id(101), fxt_ote_id(102)
        # fmt: off
        score_0: ActiveScore = fxt_active_score_factory(
            index=0, task_node_id=task_node_id, score=0.2, task_score=0.7, model_ids=[model_1_id]
        )
        score_1: ActiveScore = fxt_active_score_factory(
            index=1, task_node_id=task_node_id, score=0.3, task_score=0.3, model_ids=[model_1_id]
        )
        score_2: ActiveScore = fxt_active_score_factory(
            index=2, task_node_id=task_node_id, score=0.4, task_score=0.1, model_ids=[model_1_id]
        )
        score_3: ActiveScore = fxt_active_score_factory(
            index=3, task_node_id=task_node_id, score=0.5, task_score=0.5, model_ids=[model_2_id]
        )
        # fmt: on
        score_4, score_5 = tuple(
            ActiveScore.make_default(
                id_=ActiveScoreRepo.generate_id(),
                media_identifier=fxt_media_identifier_factory(i),
                task_nodes_ids=[task_node_id],
            )
            for i in (4, 5)
        )
        scores = [score_0, score_1, score_2, score_3, score_4, score_5]
        identifiers = [score.media_identifier for score in scores]
        repo.save_many(scores)
        candidates = [identifiers[0], identifiers[1], identifiers[3]]

        best_items = repo.find_best_candidates(
            candidate_media=candidates,
            size=2,
            task_node_id=task_node_id,
            inferred_only=mapped_only,
            models_ids=([model_1_id]) if consider_model else None,
        )

        if consider_model:
            # the output should contain score_1 and score_0 because score_2 is not
            # in the candidates list, while score_3 refers to another model.
            assert best_items == (
                ActiveScoreSuggestionInfo(media_identifier=identifiers[1], score=0.3, models_ids=(model_1_id,)),
                ActiveScoreSuggestionInfo(media_identifier=identifiers[0], score=0.7, models_ids=(model_1_id,)),
            )
        else:
            # the output should contain score_1 and score_3 because score_2 is not
            # in the candidates list; the model does not matter
            assert best_items == (
                ActiveScoreSuggestionInfo(media_identifier=identifiers[1], score=0.3, models_ids=(model_1_id,)),
                ActiveScoreSuggestionInfo(media_identifier=identifiers[3], score=0.5, models_ids=(model_2_id,)),
            )

        best_items = repo.find_best_candidates(
            candidate_media=identifiers,
            size=5,
            inferred_only=mapped_only,
            models_ids=([model_1_id]) if consider_model else None,
        )
        best_media_ids = {item.media_identifier for item in best_items}

        if mapped_only:
            # the output should contain all and only the 4 existing mapped scores
            # score_4 and score_5 are excluded because not-inferred.
            assert len(best_media_ids) == 4
            assert best_media_ids == set(identifiers[:4])
        else:
            # the output should contain the 4 existing mapped scores plus one between
            # score_4 and score_5. In total, 5 elements.
            assert len(best_media_ids) == 5
            assert set(identifiers[:4]).issubset(best_media_ids)

    def test_find_unmapped_candidates(
        self,
        request,
        fxt_project,
        fxt_dataset_storage,
        fxt_active_score_factory,
        fxt_media_identifier_factory,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveScoreRepo.find_unmapped_candidates
        <b>Input data:</b>
        Dataset storage
        <b>Expected results:</b>
        ActiveScoreRepo.find_unmapped_candidates returns the unmapped media
        <b>Steps</b>
        1. Create four active scores, three of which with default values
        2. Call 'find_unmapped_candidates' on two of the default items
        3. Verify that the output is contains only the unmapped items in the candidates
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        repo = ActiveScoreRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        score_1 = ActiveScore.make_default(
            id_=ActiveScoreRepo.generate_id(),
            media_identifier=fxt_media_identifier_factory(1),
            task_nodes_ids=[],
        )
        score_2 = ActiveScore.make_default(
            id_=ActiveScoreRepo.generate_id(),
            media_identifier=fxt_media_identifier_factory(2),
            task_nodes_ids=[],
        )
        score_3 = ActiveScore.make_default(
            id_=ActiveScoreRepo.generate_id(),
            media_identifier=fxt_media_identifier_factory(2),
            task_nodes_ids=[],
        )
        score_4 = fxt_active_score_factory(
            score=0.5,
            index=3,
        )
        repo.save_many((score_1, score_2, score_3, score_4))
        candidates = [
            score_1.media_identifier,
            score_2.media_identifier,
            score_4.media_identifier,
        ]

        unmapped_candidates = repo.find_unmapped_candidates(candidate_media=candidates)

        assert set(unmapped_candidates) == {
            score_1.media_identifier,
            score_2.media_identifier,
        }
