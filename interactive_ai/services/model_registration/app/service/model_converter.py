# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import ctypes
import json
import logging
import os
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from enum import Enum, auto
from pathlib import Path
from xml.etree.ElementTree import Element

from defusedxml import ElementTree
from grpc_interfaces.model_registration.pb.service_pb2 import Model, Project
from model_api.models import (
    AnomalyDetection,
    ClassificationModel,
    DetectionModel,
    KeypointDetectionModel,
    MaskRCNNModel,
    SegmentationModel,
)

from service.config import RESOURCE_MS_PORT, RESOURCE_MS_SERVICE, S3_BUCKETNAME
from service.s3client import S3Client

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_ORGANIZATION_ID = "000000000000000000000001"
LARGE_MODEL_THRESHOLD_BYTES = 50 * 1024 * 1024


class GraphVariant(Enum):
    INFERENCE = auto()
    OVMS_DEPLOYMENT = auto()


class UnsupportedModelType(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ModelConverter:
    """
    This class is responsible for converting Geti models to Modelmesh graphs
    """

    def __init__(self, s3client: S3Client) -> None:
        self.s3 = s3client

    def _get_labels(self, task_id: str, project: Project, model: str) -> list[str]:
        tree = ElementTree.parse(model)
        root = tree.getroot()
        lorder = root.find("./rt_info/model_info/label_ids")
        labels = []
        labels_ord = {}
        for task in project.pipeline.tasks:
            if task.id == task_id:
                labels_ord = {label.id: label for label in task.labels}
                labels.extend([label.name for label in task.labels])
        if lorder is not None:
            logger.info("Sorting labels")
            labels = []
            lvalues = lorder.get("value", "").split()
            emptylabel = self._get_empty_label(task_id, project)
            for label_id in lvalues:
                if label_id in labels_ord:
                    labels.append(labels_ord[label_id].name.replace(" ", "_"))
                elif emptylabel is not None:
                    labels.append(emptylabel[1])
                else:
                    labels.append("Empty")

        return labels

    def _update_label_ids(self, target: str, project: Project, task_id: str, graph_type: str) -> None:
        t_tree = ElementTree.parse(target)
        t_root = t_tree.getroot()
        if t_root.find("./rt_info/model_info/label_ids") is None:
            label_ids: list[str] | None = None
            for task in project.pipeline.tasks:
                if task.id == task_id:
                    label_ids = [label.id for label in task.labels]
            if label_ids is not None:
                # switch empty label order for MaskRCNN
                if graph_type in ("ROTATED_DETECTION", "INSTANCE_SEGMENTATION"):
                    label_ids.insert(0, label_ids.pop())
                t_model_info = t_root.find("./rt_info/model_info")
                child = Element("label_ids")
                child.set("value", " ".join(label_ids))
                t_model_info.append(child)
                t_tree.write(target)
                logger.info(f"Model {target} for task_id {task_id} updated with label_ids.")
            else:
                logger.info(f"Skipping updating label_ids for model {target} for task_id {task_id}")

    def _update_use_ellipse(self, target: str, use_ellipse: bool) -> None:
        if not use_ellipse:
            return
        t_tree = ElementTree.parse(target)
        t_root = t_tree.getroot()
        if t_root.find("./rt_info/model_info/use_ellipse_shapes") is None:
            t_model_info = t_root.find("./rt_info/model_info")
            child = Element("use_ellipse_shapes")
            child.set("value", str(use_ellipse))
            t_model_info.append(child)
            t_tree.write(target)
            logger.info(f"Model {target} updated with use_ellipse_shapes.")

    def _update_normalization_scale(self, target: str, normalization_scale: float = 1.0) -> None:
        t_tree = ElementTree.parse(target)
        t_root = t_tree.getroot()
        normalization_scale_element = t_root.find("./rt_info/model_info/normalization_scale")
        if normalization_scale_element is not None and not normalization_scale_element.get("value"):
            normalization_scale_element.set("value", str(normalization_scale))
            logger.info(f"Model {target} updated with normalization_scale={normalization_scale}.")
        else:
            logger.info(f"Model {target} normalization_scale update skipped, as it is already set.")
        t_tree.write(target)

    def _update_labels(self, target: str, labels: list[str]) -> None:
        t_tree = ElementTree.parse(target)
        t_root = t_tree.getroot()
        labels_element = t_root.find("./rt_info/model_info/labels")
        if labels_element is not None and not labels_element.get("value"):
            labels_element.set("value", " ".join(labels))
            logger.info(f"Model {target} updated with labels={labels}.")
        else:
            logger.info(f"Model {target} labels update skipped, as it is already set.")
        t_tree.write(target)

    def _update_model_type(self, target: str) -> None:
        t_tree = ElementTree.parse(target)
        t_root = t_tree.getroot()
        model_type_element = t_root.find("./rt_info/model_info/model_type")
        if model_type_element is not None and model_type_element.get("value") == "rotated_detection":
            model_type_element.set("value", "MaskRCNN")
            t_tree.write(target)
            print(f"Model type for {target} updated.")
        else:
            print(f"Skipping updating model_type for {target}.")

    def _convert_model(self, model_dir: str, export_dir: str, model: Model, project: Project) -> str:
        logger.info(f"Converting model {model.model_id} from task {model.task_id}")
        graph_type = self._get_graph_type(project=project, models=[model])
        logger.info(f"Graph type = {graph_type}")
        model_path = os.path.join(model_dir, "model", "model.xml")
        exported_model_path = os.path.join(export_dir, model.model_id, "1", "model.xml")
        labels = self._get_labels(model.task_id, project, model_path)

        if graph_type == "CLASSIFICATION":
            exportmodel = ClassificationModel.create_model(model_path, configuration={"labels": labels}, preload=False)
        elif graph_type == "DETECTION":
            exportmodel = DetectionModel.create_model(model_path, configuration={"labels": labels}, preload=False)
        elif graph_type == "KEYPOINT_DETECTION":
            exportmodel = KeypointDetectionModel.create_model(model_path, preload=False)
        elif graph_type == "ROTATED_DETECTION":
            self._update_model_type(model_path)
            exportmodel = MaskRCNNModel.create_model(model_path, configuration={"labels": labels}, preload=False)
        elif graph_type == "SEGMENTATION":
            exportmodel = SegmentationModel.create_model(model_path, configuration={"labels": labels}, preload=False)
        elif graph_type == "INSTANCE_SEGMENTATION":
            exportmodel = MaskRCNNModel.create_model(model_path, configuration={"labels": labels}, preload=False)
        elif graph_type in ("ANOMALY_CLASSIFICATION", "ANOMALY_DETECTION", "ANOMALY_SEGMENTATION"):
            exportmodel = AnomalyDetection.create_model(model_path, preload=False)
        else:
            logger.error(f"Unsupported model type: {graph_type}")
            raise UnsupportedModelType(f"Unsupported model type: {graph_type}")

        os.makedirs(os.path.dirname(exported_model_path), exist_ok=True)
        exportmodel.save(exported_model_path)
        self._update_label_ids(exported_model_path, project, model.task_id, graph_type)
        self._update_use_ellipse(exported_model_path, model.use_ellipse)
        if graph_type in ("ANOMALY_CLASSIFICATION", "ANOMALY_DETECTION", "ANOMALY_SEGMENTATION"):
            self._update_normalization_scale(exported_model_path, normalization_scale=1.0)
            self._update_labels(exported_model_path, labels=["Normal", "Anomalous"])

        del exportmodel
        # Clear the memory from the heap, so it's not calculated into pod's memory limits
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
        return graph_type

    def _create_subconfig(self, path: str, models: list[Model], num_streams: int = 1):
        try:
            os.makedirs(path, exist_ok=True)
            subconfig_file = os.path.join(path, "config.json")
            json_file = {"model_config_list": []}  # type: ignore
            for model in models:
                json_file["model_config_list"].append(
                    {
                        "config": {
                            "name": model.model_id,
                            "base_path": model.model_id,
                            "plugin_config": {"NUM_STREAMS": f"{num_streams}"},
                        }
                    }
                )
            with open(subconfig_file, "w") as file:
                json.dump(json_file, file, indent=4)

        except OSError as e:
            logger.error(f"Error creating subconfig file: {e}")
            raise

    def _get_empty_label(self, task_id: str, project: Project) -> tuple[str, str] | None:
        for task in project.pipeline.tasks:
            if task.id == task_id:
                for label in task.labels:
                    if label.is_empty:
                        return label.id, label.name

        return None

    def _get_models_ordered(self, project: Project, models: list[Model]):
        if len(models) == 1:
            return models

        connections = project.pipeline.connections
        modelsord = []
        idx = connections[0].from_id if connections[0].from_id else None
        while idx:
            task = next((task for task in project.pipeline.tasks if task.id == idx), None)
            if task:
                if task.task_type.upper() not in ("DATASET", "CROP"):
                    modelsord.extend([m for m in models if m.task_id == task.id])
                connection = next((conn for conn in connections if conn.from_id == idx), None)
                idx = connection.to_id if connection else None
            else:
                break

        return modelsord

    def _create_graph(
        self, path: str, project: Project, models: list[Model], graph_variant: GraphVariant = GraphVariant.INFERENCE
    ):
        graph_files = {
            GraphVariant.INFERENCE: "graph.pbtxt",
            GraphVariant.OVMS_DEPLOYMENT: "graph-ovms-deployment.pbtxt",
        }
        graph_type = self._get_graph_type(project=project, models=models)
        try:
            graph_in = os.path.join("service", "graphs", graph_type, graph_files[graph_variant])
            graph_out = os.path.join(path, "graph.pbtxt")
            with open(graph_in) as fin, open(graph_out, "w") as fout:
                graph = fin.read()
                modelsord = self._get_models_ordered(project, models)
                for idx, model in enumerate(modelsord):
                    graph = graph.replace(f"MODEL_NAME_{idx}", model.model_id)
                    emptylabel = self._get_empty_label(model.task_id, project)
                    if emptylabel is not None:
                        logger.info(f"Setting up emptylabel name to {emptylabel[1]} with id {emptylabel[0]} ")
                        graph = graph.replace(f"EMPTY_LABEL_ID_{idx}", emptylabel[0])
                        graph = graph.replace(f"EMPTY_LABEL_NAME_{idx}", emptylabel[1])
                fout.write(graph)
        except (OSError, shutil.Error) as e:
            logger.error(f"Error copying graph: {e}")
            raise

    def _delete_file(self, file_path: str):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.error(f"Error deleting file: {e}")
            raise

    def _delete_dir(self, dir_path: str):
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            logger.error(f"Error deleting folder: {e}")
            raise

    def _check_dir_size(self, dir_path: str):
        dir_size_bytes = 0
        for root, _, files in os.walk(dir_path):
            for file in files:
                dir_size_bytes += os.path.getsize(os.path.join(root, file))
        return dir_size_bytes

    def _get_graph_type(self, project: Project, models: list[Model]) -> str:
        if len(models) == 1:
            for task in project.pipeline.tasks:
                if task.id == models[0].task_id:
                    return task.task_type.upper()

        connections = project.pipeline.connections
        chain = []
        idx = connections[0].from_id if connections[0].from_id else None
        while idx:
            task = next((task for task in project.pipeline.tasks if task.id == idx), None)
            if task:
                if task.task_type.upper() not in ("DATASET", "CROP"):
                    chain.append(task.task_type.upper())
                connection = next((conn for conn in connections if conn.from_id == idx), None)
                idx = connection.to_id if connection else None
            else:
                break
        if len(chain) > 1:
            chain.insert(0, "CHAIN")

        return "_".join(chain)

    def _create_ovms_config_json(self, config_json_path: Path, graph_name: str) -> None:
        config_content = {"model_config_list": [], "mediapipe_config_list": [{"name": graph_name}]}
        with open(config_json_path, mode="w") as config_json_file:
            json.dump(config_content, config_json_file)

    def _render_ovms_package_docs(
        self, template_path: Path, output_path: Path, graph_name: str, ovms_image: str = "openvino/model_server"
    ) -> None:
        with open(template_path) as template_file:
            doc_file_content = template_file.read()
        doc_file_content = doc_file_content.replace("GRAPH_NAME_PLACEHOLDER", graph_name)
        doc_file_content = doc_file_content.replace("OVMS_IMAGE_PLACEHOLDER", ovms_image)

        with open(output_path, mode="w") as doc_file:
            doc_file.write(doc_file_content)

    def _copy_license_file(self, license_path: Path, output_path: Path) -> None:
        try:
            shutil.copy(license_path, output_path)
        except OSError:
            logger.exception(f"Failed to copy license ({license_path}) to OVMS package directory ({output_path})")
            raise

    def _create_ovms_graph_files(self, export_dir: str, project: Project) -> None:
        export_dir_path = Path(export_dir)
        graph_name = f"{project.id}-graph"

        # Create graph directory
        graph_dir_path = export_dir_path / graph_name
        graph_dir_path.mkdir()

        # Move all artifacts to graph directory
        for path in export_dir_path.glob("*"):
            shutil.move(path, graph_dir_path)

        # Create config.json at export_dir_path
        self._create_ovms_config_json(export_dir_path / "config.json", graph_name)

        # Rename model's config json to subconfig.json
        shutil.move(graph_dir_path / "config.json", graph_dir_path / "subconfig.json")

        # Remove redundant files
        Path(export_dir_path / f"{project.id}.zip").unlink(missing_ok=True)
        shutil.rmtree(Path(export_dir_path / "tmp"), ignore_errors=True)

        # Add documentation and license files
        self._render_ovms_package_docs(
            template_path=Path(os.path.join("service", "ovms_package_docs", "README_template.md")),
            output_path=(export_dir_path / "README.md"),
            graph_name=graph_name,
        )
        self._copy_license_file(
            license_path=Path(os.path.join("service", "ovms_package_docs", "LICENSE")),
            output_path=(export_dir_path / "LICENSE"),
        )

    def prepare_graph(
        self, project: Project, models: list[Model], graph_variant: GraphVariant = GraphVariant.INFERENCE
    ) -> str:
        """
        This function is responsible for parsing Project, download and conversion of models and
        creation of corresponding Mediapipe graphs.
        Returns a path to a directory with prepared mediapipe graphs.
        Caller of this function is responsible for cleaning up returned directory after it is no longer needed.
        """
        export_dir = tempfile.mkdtemp(prefix="exported", dir="/tmp")
        for model in models:
            filename = tempfile.mkstemp(".zip", "model", "/tmp")[1]
            model_url = (
                f"http://{RESOURCE_MS_SERVICE}:{RESOURCE_MS_PORT}"
                f"/api/v1/organizations/{model.organization_id}"
                f"/workspaces/{model.workspace_id}/projects/{model.project_id}"
                f"/model_groups/{model.model_group_id}/models/{model.model_id}"
                f"/optimized_models/{model.optimized_model_id}/export"
            )
            logger.info(f"Getting model from {model_url}")
            urllib.request.urlretrieve(model_url, filename)  # noqa: S310  # nosec
            model_dir = os.path.splitext(filename)[0]
            os.makedirs(model_dir, exist_ok=True)
            try:
                with zipfile.ZipFile(filename, "r") as zippy:
                    zippy.extractall(model_dir)
                self._delete_file(file_path=filename)
                model.model_id = f"{model.model_id}-{str(int(time.time() * 1000))}"
                self._convert_model(model_dir=model_dir, export_dir=export_dir, model=model, project=project)
                logger.info(f"Model converted successfully {model_dir}")
            except zipfile.BadZipFile:
                logger.error("Invalid zip file.")
            finally:
                self._delete_dir(dir_path=model_dir)

        num_streams = 1 if self._check_dir_size(export_dir) > LARGE_MODEL_THRESHOLD_BYTES else 2
        self._create_subconfig(export_dir, models, num_streams=num_streams)
        self._create_graph(export_dir, project, models, graph_variant=graph_variant)

        if graph_variant == graph_variant.OVMS_DEPLOYMENT:
            self._create_ovms_graph_files(export_dir=export_dir, project=project)

        return export_dir

    def process_model(self, name: str, project: Project, models: list[Model]):  # noqa: ANN201
        """
        This function calls prepare_graph method to create Mediapipe Graphs, and then uploads .
        """
        export_dir = self.prepare_graph(project=project, models=models)
        self.s3.upload_folder(
            bucket_name=S3_BUCKETNAME,
            object_key=name,
            local_folder_path=export_dir,
        )
        self._delete_dir(dir_path=export_dir)
        logger.info(f"Model converted successfully {export_dir}")
