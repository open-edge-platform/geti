# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest

from communication.rest_views.media_rest_views import MediaRESTViews

from iai_core.entities.media import MediaPreprocessingStatus


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

    @pytest.mark.parametrize("preprocessing_status", MediaPreprocessingStatus)
    def test_media_to_rest_preprocessing(self, fxt_image_entity, fxt_video_entity, fxt_project, preprocessing_status):
        """
        Test to check if the media_to_rest method exposes the preprocessing status of the media correctly
        Image and Video entities are tested. VideoFrame entity does not have preprocessing
        """
        # Arrange
        media_entities = [fxt_image_entity, fxt_video_entity]

        # Act
        for media_entity in media_entities:
            media_entity.preprocessing.status = preprocessing_status
            rest_view = MediaRESTViews.media_to_rest(
                media=media_entity,
                media_identifier=media_entity.media_identifier,
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                annotation_state_per_task=None,
            )

            # Assert
            if preprocessing_status == MediaPreprocessingStatus.FINISHED:
                assert rest_view["thumbnail"] is not None
            else:
                assert rest_view["thumbnail"] is None
