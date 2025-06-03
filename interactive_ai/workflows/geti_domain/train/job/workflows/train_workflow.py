# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Task node train workflow module
"""

from typing import Optional, Any

from flytekit import workflow

from job.tasks.evaluate_and_infer.evaluate_and_infer import evaluate_and_infer
from job.tasks.prepare_and_train.prepare_data_and_train import prepare_training_data_model_and_start_training


@workflow
def train_workflow(  # noqa: PLR0913
    project_id: str,
    task_id: str,
    from_scratch: bool,
    should_activate_model: bool,
    infer_on_pipeline: bool,
    model_storage_id: str = "",
    hyper_parameters_id: str = "",
    enable_training_from_dataset_shard: bool = True,
    max_shard_size: int = 1000,
    num_image_pulling_threads: int = 10,
    num_upload_threads: int = 2,
    max_training_dataset_size: Optional[int] = None,  # noqa: UP007,
    min_annotation_size: Optional[int] = None,  # noqa: UP007,
    max_number_of_annotations: Optional[int] = None,  # noqa: UP007,
    reshuffle_subsets: bool = False,
    # Training command
    command: list[str] = ["bash", "-c", "run"],
    keep_mlflow_artifacts: bool = False,
    hyperparameters: Optional[dict] = None,
) -> None:
    """
    Task node train workflow
    :param workspace_id: Workspace ID
    :param project_id: Project ID
    :param task_id: Task ID
    :param from_scratch: Whether to train the task from scratch.
    :param should_activate_model: Whether to activate model after training
    :param infer_on_pipeline: Whether to infer on pipeline
    :param model_storage_id: ID of model storage to train model in, use active model if empty string
    :param hyper_parameters_id: ID of the hyper-parameters configuration to use for this job.
        If unspecified, it defaults to the current configuration of the model storage.
    :param enable_training_from_dataset_shard: Whether to enable model training from dataset shard
    :param max_shard_size: Maximum number of dataset items in each shard file
    :param num_image_pulling_threads: Number of threads used for pulling image bytes
    :param num_upload_threads: Number of threads used for uploading shard files
    :param max_training_dataset_size: maximum training dataset size
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
    ignored during training
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored during training.
    :param reshuffle_subsets: Whether to reassign/shuffle all the items to subsets including Test set from scratch
    :param command: Command to be executed on the primary container, e.g., OTX2 trainer pod.
    :param keep_mlflow_artifacts: If true, do not remove the artifacts in mlflow bucket even if training succeeds.
        It would be useful for debugging.
    :param hyperparameters: Dict containing the hyperparameters to be used for training.
    """
    # Prepare training data, model entities, and mlflow bucket directory
    train_data = prepare_training_data_model_and_start_training(
        project_id=project_id,
        task_id=task_id,
        from_scratch=from_scratch,
        should_activate_model=should_activate_model,
        infer_on_pipeline=infer_on_pipeline,
        command=command,
        model_storage_id=model_storage_id,
        hyper_parameters_id=hyper_parameters_id,
        enable_training_from_dataset_shard=enable_training_from_dataset_shard,
        max_shard_size=max_shard_size,
        num_image_pulling_threads=num_image_pulling_threads,
        num_upload_threads=num_upload_threads,
        max_training_dataset_size=max_training_dataset_size,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
        reshuffle_subsets=reshuffle_subsets,
        hyperparameters=hyperparameters,
    )

    evaluate_and_infer(
        train_data=train_data,
        should_activate_model=should_activate_model,
        infer_on_pipeline=infer_on_pipeline,
        from_scratch=from_scratch,
        keep_mlflow_artifacts=keep_mlflow_artifacts,
    )
