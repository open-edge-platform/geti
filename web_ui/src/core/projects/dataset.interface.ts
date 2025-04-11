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

import { ProjectIdentifier } from './core.interface';

export interface Dataset {
    id: string;
    name: string;
    useForTraining: boolean;
    creationTime: string;
}

export type DatasetIdentifierParams = {
    projectId: string;
    datasetId: string;
};

export interface DatasetIdentifier extends ProjectIdentifier {
    datasetId: string;
}

export interface CreateDatasetBody {
    name: string;
    projectIdentifier: ProjectIdentifier;
}

export interface CreateDatasetResponseDTO {
    id: string;
    name: string;
    use_for_training: boolean;
    creation_time: string;
}

export interface CreateDatasetResponse {
    id: string;
    name: string;
    useForTraining: boolean;
    creationTime: string;
}

export interface DeleteDatasetResponse {
    result: string;
}

export interface ExportDatasetIdentifier extends DatasetIdentifier {
    saveVideoAsImages: boolean;
    exportFormat: ExportFormats;
}

export interface ExportDatasetStatusIdentifier extends DatasetIdentifier {
    exportDatasetId: string;
}

export interface ExportDatasetLSData {
    datasetName: string;
    datasetId: string;
    exportFormat: ExportFormats;
    isPrepareDone: boolean;
    exportDatasetId: string;
    downloadUrl?: string;
    size?: number;
}

export enum ExportFormats {
    VOC = 'voc',
    COCO = 'coco',
    YOLO = 'yolo',
    DATUMARO = 'datumaro',
}
