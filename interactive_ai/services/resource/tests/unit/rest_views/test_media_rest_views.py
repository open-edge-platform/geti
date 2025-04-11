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


from communication.rest_views.media_rest_views import MediaRESTViews


class TestMediaRESTViews:
    def test_media_to_rest_extension(self, fxt_image_entity, fxt_video_entity, fxt_project):
        """
        Test to check if the media_to_rest method exposes the extension of the media correctly
        Image and Video entities are tested. VideoFrame entity does not have media_info and hence no extension
        """
        # Arrange
        media_entities = [fxt_image_entity, fxt_video_entity]

        # Act
        for media_entity in media_entities:
            rest_view = MediaRESTViews.media_to_rest(
                media=media_entity,
                media_identifier=media_entity.media_identifier,
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                annotation_state_per_task=None,
            )

            # Assert
            assert rest_view["media_information"]["extension"] == media_entity.extension.value
