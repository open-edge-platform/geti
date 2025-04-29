# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
import os
from unittest.mock import patch

import datumaro as dm
import pytest
from geti_types import CTX_SESSION_VAR, ID
from jobs_common_extras.datumaro_conversion.mappers.id_mapper import MediaNameIDMapper, VideoNameIDMapper
from jobs_common_extras.datumaro_conversion.sc_extractor import ScExtractor
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.image import Image
from sc_sdk.entities.video import Video, VideoFrame

from job.repos.data_repo import ExportDataRepo
from job.repos.object_storage_repo import ObjectStorageRepo
from job.tasks.export_tasks.export_dataset_task import export_dataset_task
from tests.test_helpers import (
    ScDatasetItem,
    build_dataset_from_dataset_storage,
    check_video_annotation_ranges,
    get_dm_labels_map,
    get_sc_labels,
    get_sc_labels_map,
    get_voc_global_labels_map,
    return_none,
)


@pytest.mark.DatasetIEMsComponent
class TestExportManager:
    def setup_class(self):
        self.assert_method_mapping = {
            ("multi-class", "voc"): self._assert_classification_voc_export_valid,
            ("multi-class", "datumaro"): self._assert_datumaro_export_valid,
            ("segmentation", "coco"): self._assert_segmentation_coco_export_valid,
            ("segmentation", "datumaro"): self._assert_datumaro_export_valid,
            ("anom_class", "voc"): self._assert_classification_voc_export_valid,
            ("anom_seg", "voc"): self._assert_anom_seg_voc_export_valid,
            ("anom_det", "voc"): self._assert_anom_det_voc_export_valid,
            ("det_class", "voc"): self._assert_det_class_voc_export_valid,
            ("multi_label", "voc"): self._assert_classification_voc_export_valid,
            ("detection", "yolo"): self._assert_detection_yolo_export_valid,
            ("detection", "datumaro"): self._assert_datumaro_export_valid,
            ("anom_class", "datumaro"): self._assert_datumaro_export_valid,
            ("anom_seg", "datumaro"): self._assert_datumaro_export_valid,
            ("anom_det", "datumaro"): self._assert_datumaro_export_valid,
        }

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch.object(ObjectStorageRepo, "__init__", new=return_none)
    @patch.object(ObjectStorageRepo, "upload_file", new=return_none)
    @pytest.mark.parametrize(
        "lazy_fxt_project,test_project_type,fmt",
        [
            ("fxt_annotated_classification_project", "multi-class", "voc"),
            ("fxt_annotated_classification_project", "multi-class", "datumaro"),
            ("fxt_annotated_detection_project", "detection", "yolo"),
            ("fxt_annotated_detection_project", "detection", "datumaro"),
            ("fxt_annotated_segmentation_project", "segmentation", "coco"),
            ("fxt_annotated_segmentation_project", "segmentation", "datumaro"),
            ("fxt_annotated_anomaly_cls_project", "anom_class", "voc"),
            ("fxt_annotated_anomaly_seg_project", "anom_seg", "voc"),
            ("fxt_annotated_anomaly_det_project", "anom_det", "voc"),
            ("fxt_annotated_chained_det_cls_project", "det_class", "voc"),
            ("fxt_annotated_multi_label_project", "multi_label", "voc"),
            ("fxt_annotated_anomaly_cls_project", "anom_class", "datumaro"),
            ("fxt_annotated_anomaly_cls_project_with_video", "anom_class", "datumaro"),
            ("fxt_annotated_anomaly_det_project", "anom_det", "datumaro"),
            ("fxt_annotated_anomaly_seg_project", "anom_seg", "datumaro"),
        ],
    )
    def test_export_projects(
        self,
        lazy_fxt_project,
        test_project_type,
        fmt,
        fxt_temp_directory,
        request,
    ):
        """
        Export different projects to different supported formats
        """
        session = CTX_SESSION_VAR.get()
        project = request.getfixturevalue(lazy_fxt_project)
        dataset_storage: DatasetStorage = project.get_training_dataset_storage()
        data_repo = ExportDataRepo(root_path=fxt_temp_directory)

        with (
            patch("job.tasks.export_tasks.export_dataset_task.ExportDataRepo", return_value=data_repo),
            patch("job.tasks.export_tasks.export_dataset_task.publish_metadata_update") as mocked_publish,
            patch.dict(
                os.environ,
                {
                    "SESSION_ORGANIZATION_ID": str(session.organization_id),
                    "SESSION_WORKSPACE_ID": str(session.workspace_id),
                },
            ),
        ):
            dataset_id = export_dataset_task(
                organization_id=str(session.organization_id),
                project_id=str(project.id_),
                dataset_storage_id=str(dataset_storage.id_),
                include_unannotated=True,
                export_format=fmt,
                save_video_as_images=True,
            )
            download_url = (
                f"api/v1/organizations/{str(session.organization_id)}/workspaces/{str(project.workspace_id)}/"
                f"projects/{str(project.id_)}/datasets/{str(dataset_storage.id_)}/exports/{str(dataset_id)}/download"
            )
            args, _ = mocked_publish.call_args
            assert len(args) == 1
            assert args[0]["download_url"] == download_url  #  in args[0]
            assert args[0]["size"] > 0

        self.assert_method_mapping[(test_project_type, fmt)](dataset_storage, data_repo, ID(dataset_id))

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch.object(ObjectStorageRepo, "__init__", new=return_none)
    @patch.object(ObjectStorageRepo, "upload_file", new=return_none)
    @pytest.mark.parametrize(
        "lazy_fxt_project,test_project_type,fmt",
        [
            ("fxt_annotated_detection_project", "detection", "yolo"),
            ("fxt_annotated_detection_project", "detection", "datumaro"),
            ("fxt_annotated_anomaly_cls_project_with_video", "anom_class", "datumaro"),
        ],
    )
    def test_export_projects_with_video(
        self,
        lazy_fxt_project,
        test_project_type,
        fmt,
        fxt_temp_directory,
        request,
    ):
        """
        Export different projects to different supported formats
        """
        session = CTX_SESSION_VAR.get()
        project = request.getfixturevalue(lazy_fxt_project)
        dataset_storage: DatasetStorage = project.get_training_dataset_storage()
        data_repo = ExportDataRepo(root_path=fxt_temp_directory)
        with (
            patch("job.tasks.export_tasks.export_dataset_task.ExportDataRepo", return_value=data_repo),
            patch("job.tasks.export_tasks.export_dataset_task.publish_metadata_update"),
            patch.dict(
                os.environ,
                {
                    "SESSION_ORGANIZATION_ID": str(session.organization_id),
                    "SESSION_WORKSPACE_ID": str(session.workspace_id),
                },
            ),
        ):
            dataset_id = export_dataset_task(
                organization_id=str(session.organization_id),
                project_id=str(project.id_),
                dataset_storage_id=str(dataset_storage.id_),
                include_unannotated=True,
                export_format=fmt,
                save_video_as_images=False,
            )

        self.assert_method_mapping[(test_project_type, fmt)](
            dataset_storage, data_repo, ID(dataset_id), save_video_as_images=False
        )

    @staticmethod
    def _assert_media_files(
        dataset_storage: DatasetStorage,
        file_repo: ExportDataRepo,
        dataset_id: ID,
        image_subdirs: tuple[str, ...],
        image_extension: str | None = None,
        video_subdirs: tuple[str, ...] | None = None,
    ) -> tuple[list[ScDatasetItem], str]:
        """
        Check the exported images.
        Return SC.Dataset and the path of the exported dataset.
        """

        dataset = build_dataset_from_dataset_storage(dataset_storage, not video_subdirs)
        name_mapper = MediaNameIDMapper()
        dataset_path = file_repo.get_dataset_directory(dataset_id)
        images_folder = os.path.join(dataset_path, *image_subdirs)
        actual_images = [
            os.path.splitext(fname)[0]
            for fname in os.listdir(images_folder)
            if image_extension is None or os.path.splitext(fname)[-1] == image_extension
        ]
        if video_subdirs:
            expected_images = []
            expected_videos = set()
            video_mapper = VideoNameIDMapper()
            for data in dataset:
                if isinstance(data.media, Image):
                    expected_images.append(name_mapper.forward(data))
                elif isinstance(data.media, VideoFrame):
                    expected_videos.add(video_mapper.forward(data.media.video))
                elif isinstance(data.media, Video):
                    expected_videos.add(video_mapper.forward(data.media))
                else:
                    assert False, "Unsupported sc dataset item format"
            videos_folder = os.path.join(dataset_path, *video_subdirs)
            actual_videos = [os.path.splitext(fname)[0] for fname in os.listdir(videos_folder)]
            assert sorted(expected_videos) == sorted(actual_videos)
        else:
            expected_images = [name_mapper.forward(data) for data in dataset]
        # assert the filenames are the same. Checks for length as well as uniqueness
        assert sorted(expected_images) == sorted(actual_images)
        return dataset, dataset_path

    @staticmethod
    def _assert_dm_label_map(dataset_storage: DatasetStorage, sc_dataset: list[ScDatasetItem], dm_dataset: dm.Dataset):
        """
        Check whether Datumaro label map is correctly exported.
        """

        sc_image_label_map = get_sc_labels_map(dataset_storage, sc_dataset)
        dm_image_label_map = get_dm_labels_map(dm_dataset)

        assert sc_image_label_map == dm_image_label_map

    @staticmethod
    def _assert_classification_voc_export_valid(
        dataset_storage: DatasetStorage, file_repo: ExportDataRepo, dataset_id: ID
    ):
        sc_dataset, dataset_path = TestExportManager._assert_media_files(
            dataset_storage,
            file_repo,
            dataset_id,
            ("JPEGImages",),
        )

        dataset_label_names = [label.name for label in get_sc_labels(dataset_storage, sc_dataset)]
        # Check that image to label map is the same before and after export
        sc_image_label_map = get_sc_labels_map(dataset_storage, sc_dataset)
        exported_image_label_map = get_voc_global_labels_map(dataset_path, dataset_label_names)
        assert sc_image_label_map == exported_image_label_map

    @staticmethod
    def _assert_segmentation_coco_export_valid(
        dataset_storage: DatasetStorage,
        file_repo: ExportDataRepo,
        dataset_id: ID,
    ):
        sc_dataset, dataset_path = TestExportManager._assert_media_files(
            dataset_storage,
            file_repo,
            dataset_id,
            (
                "images",
                "default",
            ),
        )

        annotations_path = os.path.join(dataset_path, "annotations", "instances_default.json")
        with open(annotations_path) as f:
            coco_instances = json.load(f)

        categories = coco_instances["categories"]
        coco_label_names = [cat["name"] for cat in categories]
        dataset_labels = get_sc_labels(dataset_storage, sc_dataset)
        # assert all dataset label present in coco format
        for dataset_label in dataset_labels:
            assert dataset_label.name in coco_label_names

        coco_anns = coco_instances["annotations"]

        # assert expected number of annotations
        sc_anns = []
        for item in sc_dataset:
            sc_anns += item.annotation_scene.annotations

        assert len(coco_anns) == len(sc_anns)

    @staticmethod
    def _assert_anom_seg_voc_export_valid(dataset_storage: DatasetStorage, file_repo: ExportDataRepo, dataset_id: ID):
        sc_dataset, dataset_path = TestExportManager._assert_media_files(
            dataset_storage,
            file_repo,
            dataset_id,
            ("JPEGImages",),
        )

        dataset_label_names = [label.name for label in get_sc_labels(dataset_storage, sc_dataset)]
        exported_image_label_map = get_voc_global_labels_map(dataset_path, dataset_label_names)
        sc_image_label_map = get_sc_labels_map(dataset_storage, sc_dataset)
        anomalous_images_path = os.path.join(dataset_path, "ImageSets", "Segmentation", "default.txt")
        with open(anomalous_images_path) as file:
            lines = file.readlines()
            seg_image_names = [line.strip() for line in lines]

        # assert that normal labels exported global labels and anomalous labels exported as seg
        for image_name, label_name in sc_image_label_map.items():
            if label_name == "normal":
                assert exported_image_label_map[image_name] == "normal"
            if label_name == "anomalous":
                assert image_name in seg_image_names

    @staticmethod
    def _assert_anom_det_voc_export_valid(dataset_storage: DatasetStorage, file_repo: ExportDataRepo, dataset_id: ID):
        sc_dataset, dataset_path = TestExportManager._assert_media_files(
            dataset_storage,
            file_repo,
            dataset_id,
            ("JPEGImages",),
        )

        dataset_label_names = [label.name for label in get_sc_labels(dataset_storage, sc_dataset)]
        exported_image_label_map = get_voc_global_labels_map(dataset_path, dataset_label_names)
        sc_image_label_map = get_sc_labels_map(dataset_storage, sc_dataset)
        annotations_dir = os.path.join(dataset_path, "Annotations")

        # assert that normal labels exported global labels and anomalous labels exported as
        # segmentation labels
        for image_name, label_name in sc_image_label_map.items():
            if label_name == "normal":
                assert exported_image_label_map[image_name] == "normal"
            if label_name == "anomalous":
                annotation_path = os.path.join(annotations_dir, f"{image_name}.xml")
                with open(annotation_path, encoding="utf-8") as file:
                    xml_ann = file.read()
                assert "<bndbox>" in xml_ann
                assert "<name>anomalous</name>" in xml_ann

    @staticmethod
    def _assert_det_class_voc_export_valid(dataset_storage: DatasetStorage, file_repo: ExportDataRepo, dataset_id: ID):
        """
        Check that voc dataset for detection -> classification project contains
        both classification and detection labels for bounding boxes
        """
        sc_dataset, dataset_path = TestExportManager._assert_media_files(
            dataset_storage,
            file_repo,
            dataset_id,
            ("JPEGImages",),
        )

        parsed_dataset = dm.Dataset.import_from(dataset_path, "voc")
        sc_image_label_map = get_sc_labels_map(dataset_storage, sc_dataset)
        parsed_labels: dict[str, set] = {}
        dataset_label_names = [label.name for label in get_sc_labels(dataset_storage, sc_dataset)]
        label_cat = parsed_dataset.categories()[dm.AnnotationType.label]
        for item in parsed_dataset:
            parsed_labels[item.id] = set()
            for ann in item.annotations:
                if hasattr(ann, "label"):
                    label_name = label_cat[ann.label].name
                    parsed_labels[item.id].add(label_name)
                for attr_name, attr_val in ann.attributes.items():
                    if attr_val and attr_name in dataset_label_names:
                        parsed_labels[item.id].add(attr_name)
        assert sc_image_label_map == parsed_labels

    @staticmethod
    def _assert_detection_yolo_export_valid(
        dataset_storage: DatasetStorage, file_repo: ExportDataRepo, dataset_id: ID, *args, **kwargs
    ):
        sc_dataset, dataset_path = TestExportManager._assert_media_files(
            dataset_storage,
            file_repo,
            dataset_id,
            ("obj_train_data",),
            image_extension=".jpg",
        )

        train_subset_file = os.path.join(dataset_path, "train.txt")
        with open(train_subset_file) as file:
            train_images = file.read()

        name_mapper = MediaNameIDMapper()
        for item in sc_dataset:
            image_name = name_mapper.forward(item)
            assert image_name in train_images
            annotations_dir = os.path.join(dataset_path, "obj_train_data")
            assert len(os.listdir(annotations_dir)) == 2 * len(sc_dataset)

    @staticmethod
    def _assert_datumaro_export_valid(
        dataset_storage: DatasetStorage, file_repo: ExportDataRepo, dataset_id: ID, *args, **kwargs
    ):
        save_video_as_images = kwargs.get("save_video_as_images", True)

        sc_dataset, dataset_path = TestExportManager._assert_media_files(
            dataset_storage=dataset_storage,
            file_repo=file_repo,
            dataset_id=dataset_id,
            image_subdirs=("images", "default"),
            video_subdirs=("videos", "default") if not save_video_as_images else None,
        )

        dm_dataset = dm.Dataset.import_from(dataset_path)
        TestExportManager._assert_dm_label_map(dataset_storage, sc_dataset, dm_dataset)

        # assert expected number of annotations
        sc_anns = []
        for sc_item in sc_dataset:
            sc_anns += sc_item.annotation_scene.annotations

        dm_anns = []
        has_video = False
        for dm_item in dm_dataset:
            if isinstance(dm_item.media, dm.Image | dm.VideoFrame):
                dm_anns += dm_item.annotations
            elif isinstance(dm_item.media, dm.Video):
                has_video = True

        assert len(sc_anns) == len(dm_anns)

        # video annotation range
        if save_video_as_images:
            assert has_video is False
        else:
            check_video_annotation_ranges(
                dm_dataset=dm_dataset,
                dataset_storage=dataset_storage,
            )

        sc_exportor_version = dm_dataset.infos().get("ScExtractorVersion", "")
        assert sc_exportor_version == ScExtractor.VERSION
