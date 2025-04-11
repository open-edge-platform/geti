#
# INTEL CONFIDENTIAL
# Copyright (c) 2022 Intel Corporation
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material contains trade secrets and proprietary
# and confidential information of Intel or its suppliers and licensors. The
# Material is protected by worldwide copyright and trade secret laws and treaty
# provisions. No part of the Material may be used, copied, reproduced, modified,
# published, uploaded, posted, transmitted, distributed, or disclosed in any way
# without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#

import pytest

from sc_sdk.entities.media_score import NullMediaScore
from sc_sdk.repos import MediaScoreRepo


@pytest.mark.ScSdkComponent
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
