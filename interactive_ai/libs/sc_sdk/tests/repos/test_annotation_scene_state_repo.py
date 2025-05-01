# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy

from sc_sdk.entities.annotation_scene_state import AnnotationSceneState, AnnotationState, NullAnnotationSceneState
from sc_sdk.repos import AnnotationSceneStateRepo

from geti_types import ID, ImageIdentifier


class TestAnnotationSceneStateRepo:
    def test_annotation_scene_state_repo(self, fxt_mongo_id, request, fxt_dataset_storage_identifier) -> None:
        """
        <b>Description:</b>
        Check that AnnotationSceneStateRepo can be created and data saved/loaded/deleted to/from it.

        <b>Input data:</b>
        An empty project

        <b>Expected results:</b>
        The AnnotationSceneStateRepo correctly takes all the steps to save, fetch and delete annotation scene states.

        <b>Steps</b>
        1. Initialize the AnnotationSceneStateRepo
        2. Create a AnnotationSceneState and save it to the repo
        3. Fetch the state from the repo and check that it's retrieved correctly
        4. Update the AnnotationSceneState and save it again, check that it's retrieved correctly
        5. Delete the AnnotationSceneState, fetch it and check that a NullAnnotationSceneState is retrieved
        """
        ann_scene_state_repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: ann_scene_state_repo.delete_all())

        annotation_scene_state = AnnotationSceneState(
            media_identifier=ImageIdentifier(image_id=ID(fxt_mongo_id(0))),
            annotation_scene_id=fxt_mongo_id(1),
            annotation_state_per_task={
                fxt_mongo_id(2): AnnotationState.ANNOTATED,
                fxt_mongo_id(3): AnnotationState.PARTIALLY_ANNOTATED,
                fxt_mongo_id(4): AnnotationState.NONE,
            },
            unannotated_rois={
                fxt_mongo_id(2): [fxt_mongo_id(5)],
                fxt_mongo_id(3): [fxt_mongo_id(6)],
                fxt_mongo_id(4): [fxt_mongo_id(7)],
            },
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        ann_scene_state_repo.save(annotation_scene_state)

        reloaded_annotation_scene_state = ann_scene_state_repo.get_by_id(annotation_scene_state.id_)
        assert reloaded_annotation_scene_state == annotation_scene_state

        reloaded_annotation_scene_state.state_per_task[fxt_mongo_id(4)] = AnnotationState.ANNOTATED
        reloaded_annotation_scene_state.unannotated_rois[fxt_mongo_id(4)] = [fxt_mongo_id(8)]
        ann_scene_state_repo.save(reloaded_annotation_scene_state)
        updated_annotation_scene_state = ann_scene_state_repo.get_by_id(annotation_scene_state.id_)
        assert updated_annotation_scene_state.state_per_task[fxt_mongo_id(4)] == AnnotationState.ANNOTATED
        assert updated_annotation_scene_state.unannotated_rois[fxt_mongo_id(4)] == [fxt_mongo_id(8)]

        ann_scene_state_repo.delete_by_id(annotation_scene_state.id_)
        deleted_annotation_scene_state = ann_scene_state_repo.get_by_id(annotation_scene_state.id_)
        assert deleted_annotation_scene_state == NullAnnotationSceneState()

    def test_get_all_by_state_for_task_single_task(self, fxt_mongo_id, request, fxt_dataset_storage_identifier) -> None:
        """
        <b>Description:</b>
        Check that the get_all_by_state_for_task returns the latest state for the
        media identifier in a scenario with a single task node

        <b>Input data:</b>
        A dataset storage

        <b>Expected results:</b>
        The right AnnotationState's are found

        <b>Steps</b>
        1. Initiate AnnotationSceneStateRepo
        3. Create some annotated and some partially annotated states w.r.t one task
        3. Query the repo for unannotated/partially annotated states and assert the correct states are found
        """
        # Step 1
        repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Step 2
        task_id = fxt_mongo_id(0)
        annotated_states = []
        partially_annotated_states = []
        for i in range(1, 5):
            state = AnnotationSceneState(
                media_identifier=ImageIdentifier(image_id=ID(fxt_mongo_id(i))),
                annotation_scene_id=fxt_mongo_id(i + 10),
                annotation_state_per_task={task_id: AnnotationState.ANNOTATED},
                unannotated_rois={task_id: []},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            repo.save(state)
            annotated_states.append(state)

        for i in range(5, 10):
            state = AnnotationSceneState(
                media_identifier=ImageIdentifier(image_id=ID(fxt_mongo_id(i))),
                annotation_scene_id=fxt_mongo_id(i + 10),
                annotation_state_per_task={task_id: AnnotationState.PARTIALLY_ANNOTATED},
                unannotated_rois={task_id: []},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            repo.save(state)
            partially_annotated_states.append(state)

        # Step 3
        annotated_states_from_repo = repo.get_all_by_state_for_task(
            matchable_annotation_states_per_task={task_id: [AnnotationState.ANNOTATED]}
        )
        partially_annotated_states_from_repo = repo.get_all_by_state_for_task(
            matchable_annotation_states_per_task={task_id: [AnnotationState.PARTIALLY_ANNOTATED]}
        )
        all_states_from_repo = repo.get_all_by_state_for_task(
            matchable_annotation_states_per_task={
                task_id: [
                    AnnotationState.ANNOTATED,
                    AnnotationState.PARTIALLY_ANNOTATED,
                ]
            }
        )
        assert annotated_states == sorted(annotated_states_from_repo, key=lambda x: x.annotation_scene_id)
        assert partially_annotated_states == sorted(
            partially_annotated_states_from_repo, key=lambda x: x.annotation_scene_id
        )
        assert annotated_states + partially_annotated_states == sorted(
            all_states_from_repo, key=lambda x: x.annotation_scene_id
        )

    def test_get_all_by_state_for_task_chain_project(
        self, fxt_mongo_id, request, fxt_dataset_storage_identifier
    ) -> None:
        """
        <b>Description:</b>
        Check that the get_all_by_state_for_task returns the latest state for the
        media identifier in a scenario with multiple task nodes (chain)

        <b>Input data:</b>
        A dataset storage

        <b>Expected results:</b>
        The get_by_state_for_task_query only returns the latest AnnotationSceneState
        for a certain media

        <b>Steps</b>
        1. Initiate AnnotationSceneStateRepo
        2. Simulate the presence of a media that is unannotated for both tasks
        3. Verify that now there are unannotated media for the first task
        4. Step 4: Verify that there are NO media that are annotated for the first
           task but unannotated media for the second one
        5. Annotate the first task
        6. Verify that now there are media that are annotated for the first
           task but unannotated media for the second one
        7. Annotate the second task too (on the same media)
        8. Verify that there are no more unannotated media for the second task
        9. Verify that now there are fully annotated media
        """
        task1_id = fxt_mongo_id(0)
        task2_id = fxt_mongo_id(1)
        image_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id(2)))

        # Step 1: initialize repo
        repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Step 2: Simulate the presence of a media that is unannotated for both tasks
        unannotated_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=fxt_mongo_id(3),
            annotation_state_per_task={
                task1_id: AnnotationState.NONE,
                task2_id: AnnotationState.NONE,
            },
            unannotated_rois={task1_id: [], task2_id: []},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        repo.save(unannotated_state)

        # Step 3: Verify that now there are unannotated media for the first task
        found_unannotated_first_task = list(
            repo.get_all_by_state_for_task(matchable_annotation_states_per_task={task1_id: [AnnotationState.NONE]})
        )
        assert len(found_unannotated_first_task) == 1

        # Step 4: Verify that there are NO media that are annotated for the first
        #  task but unannotated media for the second one
        found_unannotated_second_task = list(
            repo.get_all_by_state_for_task(
                matchable_annotation_states_per_task={
                    task1_id: [AnnotationState.ANNOTATED],
                    task2_id: [AnnotationState.NONE],
                }
            )
        )
        assert not found_unannotated_second_task

        # Step 5: Annotate the first task
        first_task_annotated_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=fxt_mongo_id(3),
            annotation_state_per_task={
                task1_id: AnnotationState.ANNOTATED,
                task2_id: AnnotationState.NONE,
            },
            unannotated_rois={task1_id: [], task2_id: []},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        repo.save(first_task_annotated_state)

        # Step 6: Verify that now there are media that are annotated for the first
        #  task but unannotated media for the second one
        found_unannotated_second_task = list(
            repo.get_all_by_state_for_task(
                matchable_annotation_states_per_task={
                    task1_id: [AnnotationState.ANNOTATED],
                    task2_id: [AnnotationState.NONE],
                }
            )
        )
        assert len(found_unannotated_second_task) == 1

        # Step 7: Annotate the second task too (on the same media)
        all_tasks_annotated_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=fxt_mongo_id(4),
            annotation_state_per_task={
                task1_id: AnnotationState.ANNOTATED,
                task2_id: AnnotationState.ANNOTATED,
            },
            unannotated_rois={task1_id: [], task2_id: []},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        repo.save(all_tasks_annotated_state)

        # Step 8: Verify that there are no more unannotated media for the second task
        found_unannotated_second_task = list(
            repo.get_all_by_state_for_task(matchable_annotation_states_per_task={task2_id: [AnnotationState.NONE]})
        )
        assert not found_unannotated_second_task

        # Step 9: Verify that now there are fully annotated media
        found_all_tasks_annotated_state = list(
            repo.get_all_by_state_for_task(
                matchable_annotation_states_per_task={
                    task1_id: [AnnotationState.ANNOTATED],
                    task2_id: [AnnotationState.ANNOTATED],
                }
            )
        )
        assert len(found_all_tasks_annotated_state) == 1
        assert found_all_tasks_annotated_state[0] == all_tasks_annotated_state

    def test_get_latest_for_annotation_scene(
        self,
        fxt_mongo_id,
        fxt_dataset_storage_identifier,
        fxt_annotation_scene_empty,
        fxt_classification_task,
        request,
    ) -> None:
        """
        This test verifies that the `get_latest_for_annotation_scene` method returns
        the latest annotation scene state for a give annotation scene instance.

        It tests that the correct AnnotationSceneState is returned from the repo for:
            - An annotation scene for which only a single state has been saved
            - An annotation scene for which multiple annotation scene states have been
                saved. In this case only the latest should be returned.
        """
        # Arrange
        ann_scene_state_repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: ann_scene_state_repo.delete_all())
        image_identifier = ImageIdentifier(image_id=ID(fxt_mongo_id(2)))

        # Single annotation state
        fxt_annotation_scene_empty.id_ = ID(fxt_mongo_id(10))
        annotated_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=fxt_annotation_scene_empty.id_,
            annotation_state_per_task={fxt_classification_task.id_: AnnotationState.ANNOTATED},
            unannotated_rois={fxt_classification_task.id_: []},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        ann_scene_state_repo.save(annotated_state)

        # Multiple annotation states
        multi_annotation_scene = copy.deepcopy(fxt_annotation_scene_empty)
        multi_annotation_scene.id_ = ID(fxt_mongo_id(11))
        part_annotated_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=multi_annotation_scene.id_,
            annotation_state_per_task={fxt_classification_task.id_: AnnotationState.PARTIALLY_ANNOTATED},
            unannotated_rois={fxt_classification_task.id_: []},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        full_annotated_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=multi_annotation_scene.id_,
            annotation_state_per_task={fxt_classification_task.id_: AnnotationState.ANNOTATED},
            unannotated_rois={fxt_classification_task.id_: []},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        ann_scene_state_repo.save(part_annotated_state)
        ann_scene_state_repo.save(full_annotated_state)

        # Act
        retrieved_state = ann_scene_state_repo.get_latest_for_annotation_scene(fxt_annotation_scene_empty.id_)
        retrieved_state_multi = ann_scene_state_repo.get_latest_for_annotation_scene(multi_annotation_scene.id_)

        # Assert
        assert retrieved_state == annotated_state
        assert retrieved_state_multi == full_annotated_state

    def test_count_image_states(
        self,
        request,
        fxt_dataset_storage_identifier,
        fxt_image_identifier,
        fxt_mongo_id,
    ) -> None:
        """
        Checks that count_image_states_for_task counts the correct number of annotated and unannotated images, when
        multiple states are present for the same image.
        """
        ann_scene_state_repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: ann_scene_state_repo.delete_all())
        annotation_scene_state_annotated = AnnotationSceneState(
            media_identifier=fxt_image_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.ANNOTATED},
        )
        annotation_scene_state_unannotated = AnnotationSceneState(
            media_identifier=fxt_image_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.NONE},
        )
        ann_scene_state_repo.save_many([annotation_scene_state_annotated, annotation_scene_state_unannotated])

        annotated_states_count = ann_scene_state_repo.count_images_state_for_task(
            annotation_states=[AnnotationState.ANNOTATED], task_id=fxt_mongo_id(2)
        )

        unannotated_states_count = ann_scene_state_repo.count_images_state_for_task(
            annotation_states=[AnnotationState.NONE], task_id=fxt_mongo_id(2)
        )
        assert annotated_states_count == 0
        assert unannotated_states_count == 1

    def test_count_video_frame_states(
        self,
        request,
        fxt_dataset_storage_identifier,
        fxt_video_frame_identifier,
        fxt_mongo_id,
    ) -> None:
        """
        Checks that count_video_frame_states_for_task counts the correct number of annotated and unannotated frames,
        when multiple states are present for the same frame.
        """
        ann_scene_state_repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: ann_scene_state_repo.delete_all())
        annotation_scene_state_annotated = AnnotationSceneState(
            media_identifier=fxt_video_frame_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.ANNOTATED},
        )
        annotation_scene_state_unannotated = AnnotationSceneState(
            media_identifier=fxt_video_frame_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.NONE},
        )
        ann_scene_state_repo.save_many([annotation_scene_state_annotated, annotation_scene_state_unannotated])

        annotated_states_count = ann_scene_state_repo.count_video_frames_state_for_task(
            annotation_states=[AnnotationState.ANNOTATED], task_id=fxt_mongo_id(2)
        )
        unannotated_states_count = ann_scene_state_repo.count_video_frames_state_for_task(
            annotation_states=[AnnotationState.NONE], task_id=fxt_mongo_id(2)
        )
        assert annotated_states_count == 0
        assert unannotated_states_count == 1

    def test_count_video_states(
        self,
        request,
        fxt_dataset_storage_identifier,
        fxt_video_frame_identifier,
        fxt_video_frame_identifier_2,
        fxt_mongo_id,
    ) -> None:
        """
        Checks that count_video_states_for_task counts the correct number of annotated and unannotated videos,
        when multiple states are present for the same video. When a video first has two annotated frames, and then
        these same frames are updated with an unannotated state, the video should count as 1 unannotated videos and
        0 annotated videos.
        """
        ann_scene_state_repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        request.addfinalizer(lambda: ann_scene_state_repo.delete_all())
        annotation_scene_state_annotated_1 = AnnotationSceneState(
            media_identifier=fxt_video_frame_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.ANNOTATED},
        )
        annotation_scene_state_annotated_2 = AnnotationSceneState(
            media_identifier=fxt_video_frame_identifier_2,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.ANNOTATED},
        )
        annotation_scene_state_unannotated_1 = AnnotationSceneState(
            media_identifier=fxt_video_frame_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.NONE},
        )
        annotation_scene_state_unannotated_2 = AnnotationSceneState(
            media_identifier=fxt_video_frame_identifier_2,
            annotation_scene_id=fxt_mongo_id(1),
            id_=ann_scene_state_repo.generate_id(),
            unannotated_rois={fxt_mongo_id(2): []},
            annotation_state_per_task={fxt_mongo_id(2): AnnotationState.NONE},
        )
        ann_scene_state_repo.save_many(
            [
                annotation_scene_state_annotated_1,
                annotation_scene_state_annotated_2,
                annotation_scene_state_unannotated_1,
                annotation_scene_state_unannotated_2,
            ]
        )

        annotated_states_count = ann_scene_state_repo.count_videos_state_for_task(
            annotation_states=[AnnotationState.ANNOTATED], task_id=fxt_mongo_id(2)
        )
        unannotated_states_count = ann_scene_state_repo.count_videos_state_for_task(
            annotation_states=[AnnotationState.NONE], task_id=fxt_mongo_id(2)
        )
        assert annotated_states_count == 0
        assert unannotated_states_count == 1
