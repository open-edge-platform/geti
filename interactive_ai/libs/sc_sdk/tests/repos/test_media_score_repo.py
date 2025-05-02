#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#


from sc_sdk.entities.media_score import NullMediaScore
from sc_sdk.repos import MediaScoreRepo


class TestMediaScoreRepo:
    def test_media_score_repo(self, request, fxt_media_score, fxt_image_identifier, fxt_dataset_storage) -> None:
        """
        <b>Description:</b>
        Check that MediaScoreRepo behaves correctly

        <b>Input data:</b>
        MediaScore instance

        <b>Expected results:</b>
        Test succeeds if user test can be inserted in the database, retrieved and deleted.

        <b>Steps</b>
        1. Create Input data
        2. Add MediaScore to the project
        3. Retrieve the MediaScore and check that it is the right one
        3. Delete the MediaScore and check that it is deleted
        """
        media_score_repo = MediaScoreRepo(fxt_dataset_storage.identifier)
        request.addfinalizer(lambda: media_score_repo.delete_by_id(fxt_media_score.id_))

        media_score_repo.save(fxt_media_score)

        media_score_back = media_score_repo.get_by_id(fxt_media_score.id_)
        assert fxt_media_score == media_score_back

        # Delete by id
        media_score_repo.delete_by_id(fxt_media_score.id_)
        assert media_score_repo.get_by_id(fxt_media_score.id_) == NullMediaScore()

        # Delete by media id
        media_score_repo.save(fxt_media_score)
        media_score_repo.delete_all_by_media_id(media_id=fxt_image_identifier.media_id)
        assert media_score_repo.get_by_id(fxt_media_score.id_) == NullMediaScore()

        # Delete by model test result
        media_score_repo.save(fxt_media_score)
        media_score_repo.delete_all_by_model_test_result_id(model_test_result_id=fxt_media_score.model_test_result_id)
        assert media_score_repo.get_by_id(fxt_media_score.id_) == NullMediaScore()
