// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';
import * as yup from 'yup';

import { LabelItemType, LabelTreeItem } from '../../core/labels/label-tree-view.interface';
import { getFlattenedLabels } from '../../core/labels/utils';
import { DOMAIN } from '../../core/projects/core.interface';
import { isAnomalyDomain } from '../../core/projects/domains';

const NOT_EMPTY_LABELS_VALIDATION_MESSAGE = (domain: DOMAIN): string => {
    if (domain === DOMAIN.CLASSIFICATION) {
        return 'You should add at least two top level labels';
    } else {
        return 'You should add at least one label';
    }
};

export const MIN_NUMBER_OF_LABELS_FOR_CLASSIFICATION = 2;

export const MIN_POINTS_MESSAGE = 'The template requires at least one point to be defined.';
export const EMPTY_LABEL_MESSAGE = 'All labels must contain a valid name';

// User can create a project when:
// 1) the domain is one of the Anomaly ones
// 2) the domain is classification and the user has at least 2 labelRoots
// 3) 1 label if not classification
// 4) there is no empty labels
export const validateLabelsSchema = (domain: DOMAIN): yup.Schema<{ labels?: LabelTreeItem[] | undefined }> =>
    yup.object({
        labels: yup
            .array()
            .test('notEnough', NOT_EMPTY_LABELS_VALIDATION_MESSAGE(domain), (treeItems?: LabelTreeItem[]): boolean => {
                if (isAnomalyDomain(domain)) {
                    return true;
                } else if (domain === DOMAIN.CLASSIFICATION) {
                    if (!treeItems) {
                        return false;
                    }
                    // Get first level labels and labels of first level groups
                    const labelRoots = treeItems.reduce((previous: LabelTreeItem[], current: LabelTreeItem) => {
                        const rootLabels = current.type === LabelItemType.LABEL ? [current] : current.children;

                        return [...previous, ...rootLabels];
                    }, []);
                    return labelRoots.length >= MIN_NUMBER_OF_LABELS_FOR_CLASSIFICATION;
                } else {
                    const labels = treeItems && getFlattenedLabels(treeItems);
                    return !!labels && labels.length > 0;
                }
            }),
    });

export const getDuplicateLabelNames = (names: string[]) => {
    const duplicates = new Set();
    const nameCounts: Record<string, number> = {};

    for (const item of names) {
        if (nameCounts[item]) {
            duplicates.add(item);
        } else {
            nameCounts[item] = 1;
        }
    }

    return [...duplicates];
};

export const getLabelsNamesErrors = (names: string[]) => {
    if (names.length < 1) {
        return MIN_POINTS_MESSAGE;
    }

    const duplicates = getDuplicateLabelNames(names);
    const hasEmptyNames = names.some((name) => name === '');

    if (hasEmptyNames) {
        return EMPTY_LABEL_MESSAGE;
    }

    if (!isEmpty(duplicates)) {
        const pluralizeLabel =
            duplicates.length === 1
                ? `label "${duplicates[0]}" is duplicated`
                : `labels "${duplicates.join('" ,"')}" are duplicated`;

        return `Label names must be unique, ${pluralizeLabel}`;
    }

    return undefined;
};
