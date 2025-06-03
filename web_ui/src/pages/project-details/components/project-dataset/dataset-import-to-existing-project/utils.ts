// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { uniq } from 'lodash-es';

import { Label } from '../../../../../core/labels/label.interface';

export const KEYPOINT_DUPLICATED_LABELS = '- Duplicate labels are not allow in keypoint detection projects:';
export const KEYPOINT_MISSING_LABELS = '- The following labels require mapping:';
export const KEYPOINT_ANNOTATION_WARNING =
    '- Due to incomplete label mapping, annotations will be removed. Consider importing as a new project instead.';

export const hasDuplicatedValues = (data?: Record<string, string>) => {
    const values = Object.values(data ?? {});
    return uniq(values).length !== values.length;
};

export const areAllLabelsIncluded = (labels: Label[], labelsMap?: Record<string, string>) => {
    const values = Object.values(labelsMap ?? {});
    return labels.some((label) => !values.includes(label.id));
};

export const getDuplicates = (items: string[]) =>
    uniq(items.filter((value, index, array) => array.indexOf(value) !== index));
