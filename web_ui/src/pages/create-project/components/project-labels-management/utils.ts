// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { LabelTreeItem } from '../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import {
    isClassificationDomain,
    isDetectionDomain,
    isRotatedDetectionDomain,
    isSegmentationDomain,
} from '../../../../core/projects/domains';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { LABEL_TREE_TYPE } from './label-tree-type.enum';

export const getLabelTreeType = (domain: DOMAIN, firstInChain: boolean): LABEL_TREE_TYPE => {
    if (firstInChain) {
        return LABEL_TREE_TYPE.SINGLE;
    } else if (domain === DOMAIN.CLASSIFICATION) {
        return LABEL_TREE_TYPE.HIERARCHY;
    } else {
        return LABEL_TREE_TYPE.FLAT;
    }
};

export const getProjectLabels = (tasksLabels: TaskMetadata[]): LabelTreeItem[] => {
    return tasksLabels.flatMap((task) => task.labels);
};

export const getTutorialCardKey = (
    domain: DOMAIN,
    isTaskChain: boolean,
    relation: LabelsRelationType
): TUTORIAL_CARD_KEYS | undefined => {
    const isDetection = isDetectionDomain(domain) || isRotatedDetectionDomain(domain);
    const isSegmentation = isSegmentationDomain(domain);
    const isSingleSelectionClassification =
        isClassificationDomain(domain) && relation === LabelsRelationType.SINGLE_SELECTION;
    const isMultipleSelectionClassification =
        isClassificationDomain(domain) && relation === LabelsRelationType.MULTI_SELECTION;
    const isMixedClassification = isClassificationDomain(domain) && relation === LabelsRelationType.MIXED;

    if (isDetection && isTaskChain) {
        return TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION_CHAIN;
    } else if (isDetection) {
        return TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION;
    } else if (isSegmentation) {
        return TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_SEGMENTATION;
    } else if (isSingleSelectionClassification) {
        return TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_SINGLE_SELECTION;
    } else if (isMultipleSelectionClassification) {
        return TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_MULTIPLE_SELECTION;
    } else if (isMixedClassification) {
        return TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_HIERARCHICAL;
    }
};

export const validateColor = (input: string | undefined) => {
    const validatedColor = input?.split('#')[1];
    if (!validatedColor) {
        return '#000000';
    } else if (validatedColor.length === 3) {
        //eslint-disable-next-line max-len
        return `#${validatedColor[0]}${validatedColor[0]}${validatedColor[1]}${validatedColor[1]}${validatedColor[2]}${validatedColor[2]}`;
    } else if (/^#[0-9A-F]{6}$/i.test(input)) {
        return input;
    }
    return `#${'0'.repeat(6 - validatedColor.length)}${validatedColor}`;
};
