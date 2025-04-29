// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DatasetIdentifier } from '../../projects/dataset.interface';

export interface ObjectsPerLabelInterface {
    id: string;
    color: string;
    name: string;
    value: number;
}

interface ObjectDistributionAspectRatio {
    balanced: number;
    tall: number;
    wide: number;
}

export interface ObjectSizeDistributionDTO {
    cluster_center: [number, number];
    cluster_width_height: [number, number];
    color: string;
    id: string;
    name: string;
    aspect_ratio_threshold_tall: number | null;
    aspect_ratio_threshold_wide: number | null;
    size_distribution: [number, number][];
    object_distribution_from_aspect_ratio: ObjectDistributionAspectRatio;
}

export interface AllTaskDatasetStatisticsDTO {
    tasks: TaskDatasetStatisticsDTO[];
    overview: Omit<DatasetStatisticsDTO, 'objects_per_label' | 'object_size_distribution_per_label'>;
}

export interface TaskDatasetStatisticsDTO extends DatasetStatisticsDTO {
    task_id: string;
}

export interface DatasetStatisticsDTO {
    images: number;
    videos: number;
    annotated_images: number;
    annotated_videos: number;
    annotated_frames: number;
    objects_per_label: ObjectsPerLabelInterface[];
    object_size_distribution_per_label: ObjectSizeDistributionDTO[];
}

export interface TaskIdentifier extends DatasetIdentifier {
    taskId?: string | null;
}
