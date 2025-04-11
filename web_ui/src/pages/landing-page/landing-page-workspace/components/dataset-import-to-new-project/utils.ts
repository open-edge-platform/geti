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

import isEmpty from 'lodash/isEmpty';

import { DATASET_IMPORT_DOMAIN, DATASET_IMPORT_TASK_TYPE } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportLabel, DatasetImportSupportedProjectType } from '../../../../../core/datasets/dataset.interface';
import { TASK_TYPE_TO_DOMAIN } from '../../../../../core/datasets/utils';

// Finds item in provided collection of object if it exists
const findInScope = (scope: Record<string, unknown>[], find: string): Record<string, unknown> | undefined => {
    for (const scopeItem of scope) {
        const { label, group } = scopeItem;

        if (find === label || find === group) return scopeItem;
    }
};

// Returns a single object with nested structure encapsulated within a children property for each path segment
const buildLabelStructureFromPathSegments = (scope: Record<string, unknown>[], pathSegments: string[]): void => {
    const current: string | undefined = pathSegments.shift();

    if (!current) return;

    let found: Record<string, unknown> | undefined = findInScope(scope, current.replace('@', ''));

    if (!found) {
        scope.push(
            (found = {
                [current[0] === '@' ? 'group' : 'label']: current.replace('@', ''),
            })
        );
    }

    if (!isEmpty(pathSegments)) {
        found.children = found.children || [];

        buildLabelStructureFromPathSegments(found.children as Record<string, unknown>[], pathSegments);
    }
};

// Returns an array of objects with nested structure encapsulated within a children property
export const getLabelsStructureFromPaths = (paths: string[]): Record<string, unknown>[] => {
    const labelsStructure: Record<string, unknown>[] = [];

    paths.forEach((path: string) => buildLabelStructureFromPathSegments(labelsStructure, path.split('>')));

    return labelsStructure;
};

// Method returns "fullpath" string of the label including all the parent labels and groups
// Labels hierarchy separated by ">", groups use "@" notation (@<some_group_name>)
export const getLabelFullPath = (labelName: string, labels: DatasetImportLabel[]): string => {
    const label: DatasetImportLabel | undefined = labels.find(
        (labelItem: DatasetImportLabel) => labelItem.name === labelName
    );

    if (!label) return labelName;

    const { parent, group, name } = label;

    return `${parent ? getLabelFullPath(parent, labels) + '>' : ''}${group ? '@' + group + '>' : ''}${name}`;
};

export const getDatasetImportDomain = (
    taskType: DATASET_IMPORT_TASK_TYPE,
    anomalyRevamp: boolean
): DATASET_IMPORT_DOMAIN | undefined => {
    if (anomalyRevamp && taskType === DATASET_IMPORT_TASK_TYPE.ANOMALY_CLASSIFICATION) {
        return TASK_TYPE_TO_DOMAIN[DATASET_IMPORT_TASK_TYPE.ANOMALY_DETECTION];
    }
    return TASK_TYPE_TO_DOMAIN[taskType];
};

export const sortProjectTypes = (
    projectTypes: DatasetImportSupportedProjectType[]
): DatasetImportSupportedProjectType[] => {
    return projectTypes.sort(
        (first: DatasetImportSupportedProjectType, second: DatasetImportSupportedProjectType): number =>
            first.projectType >= second.projectType ? 1 : -1
    );
};

export const isTaskChainedProject = (taskType: DATASET_IMPORT_TASK_TYPE | null): boolean => {
    return (
        taskType === DATASET_IMPORT_TASK_TYPE.DETECTION_CLASSIFICATION ||
        taskType === DATASET_IMPORT_TASK_TYPE.DETECTION_SEGMENTATION
    );
};
