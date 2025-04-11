// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
