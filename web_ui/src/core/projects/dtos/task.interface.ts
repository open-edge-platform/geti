// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ExportStatusStateDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';
import { EditedLabelDTO, LabelCreation } from '../../labels/dtos/label.interface';

export enum TASK_TYPE {
    ANOMALY = 'anomaly',
    ANOMALY_CLASSIFICATION = 'anomaly_classification',
    ANOMALY_DETECTION = 'anomaly_detection',
    ANOMALY_SEGMENTATION = 'anomaly_segmentation',
    CLASSIFICATION = 'classification',
    CROP = 'crop',
    DETECTION = 'detection',
    DETECTION_ROTATED_BOUNDING_BOX = 'rotated_detection',
    SEGMENTATION = 'segmentation',
    SEGMENTATION_INSTANCE = 'instance_segmentation',
    DATASET = 'dataset',
    KEYPOINT_DETECTION = 'keypoint_detection',
}

export interface DatasetTask {
    task_type: TASK_TYPE.DATASET;
    title: 'Dataset';
}

export interface CropTask {
    task_type: TASK_TYPE.CROP;
    title: 'Crop';
}

type AnomalyTaskType = TASK_TYPE.ANOMALY_CLASSIFICATION | TASK_TYPE.ANOMALY_DETECTION | TASK_TYPE.ANOMALY_SEGMENTATION;
interface AnomalyTask {
    task_type: AnomalyTaskType;
    title: 'Anomaly';
}

interface TaskCommon {
    task_type: TASK_TYPE;
    title: string;
}

export type TaskCreation = AnomalyTask | DatasetTask | CropTask | NotDefaultTaskCreation | KeypointTaskCreation;

interface NotDefaultTaskCreation extends TaskCommon {
    labels: LabelCreation[];
}

export interface KeypointStructureDTO {
    edges: { nodes: [string, string] }[];
    positions: { label: string; x: number; y: number }[];
}

export interface KeypointTaskCreation extends NotDefaultTaskCreation {
    keypoint_structure: KeypointStructureDTO;
    task_type: TASK_TYPE.KEYPOINT_DETECTION;
}

export interface TaskDTO extends TaskCommon {
    id: string;
    labels?: EditedLabelDTO[];
}

export interface KeypointTaskDTO extends TaskDTO {
    keypoint_structure: KeypointStructureDTO;
}

export interface ProjectExportStatusDTO {
    state: ExportStatusStateDTO;
    progress: number;
    download_url: string | null;
}

export interface ProjectImportStatusDTO {
    state: ExportStatusStateDTO;
    progress: number;
    project_id: string | null;
}

export interface ProjectExportDTO {
    job_id: string;
}

export interface ProjectImportDTO {
    job_id: string;
}
