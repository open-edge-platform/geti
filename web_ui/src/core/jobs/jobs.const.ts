// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

export const GETI_SYSTEM_AUTHOR_ID = 'geti';

export enum JobState {
    RUNNING = 'running',
    FINISHED = 'finished',
    SCHEDULED = 'scheduled',
    CANCELLED = 'cancelled',
    FAILED = 'failed',
}

export enum JobStepState {
    FINISHED = 'finished',
    RUNNING = 'running',
    WAITING = 'waiting',
    SKIPPED = 'skipped',
    FAILED = 'failed',
    CANCELLED = 'cancelled',
}

export enum JobType {
    TRAIN = 'train',
    TEST = 'test',
    OPTIMIZATION_POT = 'optimize_pot',
    EXPORT_DATASET = 'export_dataset',
    PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT = 'prepare_import_to_new_project',
    PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT = 'perform_import_to_new_project',
    PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT = 'prepare_import_to_existing_project',
    PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT = 'perform_import_to_existing_project',
    EXPORT_PROJECT = 'export_project',
    IMPORT_PROJECT = 'import_project',
}

export const JobTypePayload: { [key in JobType]: string } = {
    [JobType.TRAIN]: 'train',
    [JobType.TEST]: 'test',
    [JobType.OPTIMIZATION_POT]: 'optimize_pot',
    [JobType.EXPORT_DATASET]: 'export_dataset',
    [JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT]: 'prepare_import_to_new_project',
    [JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT]: 'perform_import_to_new_project',
    [JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT]: 'prepare_import_to_existing_project',
    [JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT]: 'perform_import_to_existing_project',
    [JobType.EXPORT_PROJECT]: 'export_project',
    [JobType.IMPORT_PROJECT]: 'import_project',
};
