# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from operator import attrgetter

import pytest
from testfixtures import compare

from active_learning.entities import ActiveSuggestion, NullActiveSuggestion
from active_learning.storage.repos import ActiveSuggestionRepo

from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier, VideoIdentifier


@pytest.fixture
def fxt_active_suggestion_factory(fxt_ote_id, fxt_media_identifier_factory):
    def _build_active_suggestion(index: int, media_identifier: MediaIdentifierEntity | None = None) -> ActiveSuggestion:
        if media_identifier is None:
            media_identifier = fxt_media_identifier_factory(index)
        return ActiveSuggestion(
            id_=fxt_ote_id(index),
            media_identifier=media_identifier,
            score=0.7,
            models=[fxt_ote_id(2), fxt_ote_id(3)],
            user="user",
            reason="reason",
        )

    return _build_active_suggestion


class TestActiveSuggestionRepo:
    def test_save_and_load(self, request, fxt_ote_id, fxt_active_suggestion_factory) -> None:
        """
        <b>Description:</b>
        Check that ActiveSuggestionRepo can save and retrieve ActiveSuggestion items.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        The ActiveSuggestion entities can be saved to the database and pulled from it.

        <b>Steps</b>
        1. Create an active suggestion S1
        2. Save S1
        3. Load S1 from the repo and verify that it matches the original object
        4. Create an active suggestion S2
        5. Save S2
        6. Reload both S1 and S2 and verify that they match the original objects
        """
        suggestion_1 = fxt_active_suggestion_factory(1)
        assert suggestion_1.ephemeral
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = ActiveSuggestionRepo(dataset_storage_identifier=dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save(suggestion_1)
        assert not suggestion_1.ephemeral
        suggestion_1_reloaded = repo.get_by_id(suggestion_1.id_)
        compare(suggestion_1_reloaded, suggestion_1, ignore_eq=True)

        repo.save(suggestion_1_reloaded)
        suggestion_1_reloaded_again = repo.get_by_id(suggestion_1.id_)
        compare(suggestion_1_reloaded_again, suggestion_1, ignore_eq=True)

        suggestion_2 = fxt_active_suggestion_factory(2)
        repo.save(suggestion_2)
        suggestion_1_reloaded = repo.get_by_id(suggestion_1.id_)
        suggestion_2_reloaded = repo.get_by_id(suggestion_2.id_)
        compare(suggestion_1_reloaded, suggestion_1, ignore_eq=True)
        compare(suggestion_2_reloaded, suggestion_2, ignore_eq=True)

    def test_save_many(self, request, fxt_ote_id, fxt_active_suggestion_factory) -> None:
        """
        <b>Description:</b>
        Test the method ActiveSuggestionRepo.save_many.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        The ActiveSuggestion entities can be saved in bulk and retrieved

        <b>Steps</b>
        1. Create an active suggestion S1
        2. Save S1
        3. Load S1 from the repo and verify that it matches the original object
        4. Create an active suggestion S2
        5. Save S2
        6. Reload both S1 and S2 and verify that they match the original objects
        """
        suggestion_1 = fxt_active_suggestion_factory(1)
        suggestion_2 = fxt_active_suggestion_factory(2)
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = ActiveSuggestionRepo(dataset_storage_identifier=dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save_many([suggestion_1, suggestion_2])

        assert not suggestion_1.ephemeral
        assert not suggestion_2.ephemeral
        suggestion_1_reloaded = repo.get_by_id(suggestion_1.id_)
        suggestion_2_reloaded = repo.get_by_id(suggestion_2.id_)
        compare(suggestion_1_reloaded, suggestion_1, ignore_eq=True)
        compare(suggestion_2_reloaded, suggestion_2, ignore_eq=True)

    def test_get_by_id(self, request, fxt_ote_id, fxt_active_suggestion_factory) -> None:
        """
        <b>Description:</b>
        Test the method ActiveSuggestionRepo.get_by_id.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveSuggestionRepo.get_by_id can retrieve the right item if it exists.

        <b>Steps</b>
        1. Create and save two active suggestions
        2. Call `get_by_id` to reload the first suggestion
        3. Check that the returned object matches the original one
        4. Call `get_by_id` to load a non-existing object
        5. Check that no actual suggestion is returned
        """
        suggestions = [fxt_active_suggestion_factory(i) for i in range(2)]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = ActiveSuggestionRepo(dataset_storage_identifier=dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        for sug in suggestions:
            repo.save(sug)

        first_suggestion_reloaded = repo.get_by_id(suggestions[0].id_)
        compare(first_suggestion_reloaded, suggestions[0], ignore_eq=True)

        non_exist_suggestion = repo.get_by_id(fxt_ote_id(123456789))
        assert isinstance(non_exist_suggestion, NullActiveSuggestion)

    def test_get_by_media_identifier(
        self,
        request,
        fxt_ote_id,
        fxt_active_suggestion_factory,
        fxt_media_identifier_factory,
    ) -> None:
        """
        <b>Description:</b>
        Test the method ActiveSuggestionRepo.get_by_media_identifier.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveSuggestionRepo.get_by_media_identifier can retrieve the right item
        if it exists.

        <b>Steps</b>
        1. Create and save two active suggestions
        2. Call `get_by_media_identifier` to reload the first suggestion
        3. Check that the returned object matches the original one
        4. Call `get_by_media_identifier` to load a non-existing object
        5. Check that no actual suggestion is returned
        """
        suggestions = [fxt_active_suggestion_factory(i) for i in range(2)]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = ActiveSuggestionRepo(dataset_storage_identifier=dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        for sug in suggestions:
            repo.save(sug)

        first_suggestion_reloaded = repo.get_by_media_identifier(suggestions[0].media_identifier)
        compare(first_suggestion_reloaded, suggestions[0], ignore_eq=True)

        non_exist_suggestion = repo.get_by_media_identifier(fxt_media_identifier_factory(123456789))
        assert isinstance(non_exist_suggestion, NullActiveSuggestion)

    def test_get_all(self, request, fxt_ote_id, fxt_active_suggestion_factory) -> None:
        """
        <b>Description:</b>
        Test the method ActiveSuggestionRepo.get_all.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveSuggestionRepo.get_all pulls all the items.

        <b>Steps</b>
        1. Create and save two active suggestions
        2. Call `get_all`
        3. Check that all the items are returned
        """
        suggestions = [fxt_active_suggestion_factory(i) for i in range(2)]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = ActiveSuggestionRepo(dataset_storage_identifier=dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        for sug in suggestions:
            repo.save(sug)

        suggestions_reloaded = list(repo.get_all())

        assert len(suggestions_reloaded) == 2
        suggestions_reloaded_sorted = sorted(suggestions_reloaded, key=attrgetter("id_"))
        compare(suggestions_reloaded_sorted, suggestions, ignore_eq=True)

    def test_get_all_media_identifiers(self, request, fxt_ote_id, fxt_active_suggestion_factory) -> None:
        """
        <b>Description:</b>
        Test the method ActiveSuggestionRepo.get_all_media_identifiers.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveSuggestionRepo.get_all_media_identifiers returns all the media_identifiers

        <b>Steps</b>
        1. Create and save two active suggestions
        2. Call `get_all_media_identifiers`
        3. Check that all the media identifiers are returned
        """
        suggestions = [fxt_active_suggestion_factory(i) for i in range(2)]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = ActiveSuggestionRepo(dataset_storage_identifier=dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        for sug in suggestions:
            repo.save(sug)

        media_identifiers = repo.get_all_media_identifiers()

        assert len(media_identifiers) == 2
        assert set(media_identifiers) == {
            suggestions[0].media_identifier,
            suggestions[1].media_identifier,
        }

    def test_delete_by_media_identifier(self, request, fxt_active_suggestion_factory, fxt_ote_id) -> None:
        """
        <b>Description:</b>
        Test the method ActiveSuggestionRepo.delete_by_media_identifier.

        <b>Input data:</b>
        Dataset storage

        <b>Expected results:</b>
        ActiveSuggestionRepo.delete_by_media_identifier deletes the specified item.

        <b>Steps</b>
        1. Create and save two active suggestions
        2. Call `delete_by_media_identifier` on the first one.
        3. Check that the first suggestion is no longer available in the database,
           while the second one is.
        4. Create and save two active suggestions for video frames
        5. Call `delete_by_media_identifier` on the video identifier
        6. Check that both frames suggestions get deleted
        """
        suggestion_1 = fxt_active_suggestion_factory(1)
        suggestion_2 = fxt_active_suggestion_factory(2)
        suggestions = [suggestion_1, suggestion_2]
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = ActiveSuggestionRepo(dataset_storage_identifier=dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        for sug in suggestions:
            repo.save(sug)

        repo.delete_by_media_identifier(suggestions[0].media_identifier)

        suggestion_1_reloaded = repo.get_by_id(suggestion_1.id_)
        suggestion_2_reloaded = repo.get_by_id(suggestion_2.id_)
        assert isinstance(suggestion_1_reloaded, NullActiveSuggestion)
        compare(suggestion_2_reloaded, suggestion_2, ignore_eq=True)

        frame_1_id = VideoFrameIdentifier(video_id=ID(fxt_ote_id(9)), frame_index=1)
        frame_2_id = VideoFrameIdentifier(video_id=ID(fxt_ote_id(9)), frame_index=2)
        video_id = VideoIdentifier(video_id=ID(fxt_ote_id(9)))
        suggestion_3 = fxt_active_suggestion_factory(3, media_identifier=frame_1_id)
        suggestion_4 = fxt_active_suggestion_factory(4, media_identifier=frame_2_id)
        repo.save_many([suggestion_3, suggestion_4])

        repo.delete_by_media_identifier(video_id)

        score_3_reloaded = repo.get_by_id(suggestion_3.id_)
        score_4_reloaded = repo.get_by_id(suggestion_4.id_)
        assert isinstance(score_3_reloaded, NullActiveSuggestion)
        assert isinstance(score_4_reloaded, NullActiveSuggestion)
