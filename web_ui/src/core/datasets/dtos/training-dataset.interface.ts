// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface SubsetInfoDTO {
    training: number;
    testing: number;
    validation: number;
}

interface DatasetInfoDTO {
    videos: number;
    frames: number;
    images: number;
}

export interface TrainingDatasetDTO {
    id: string;
    subset_info: SubsetInfoDTO;
    dataset_info: DatasetInfoDTO;
    creation_time: string;
}

export interface TrainingDatasetInfoDTO {
    dataset_revision_id: string;
    dataset_storage_id: string;
    n_frames: number;
    n_images: number;
    n_samples: number;
}
