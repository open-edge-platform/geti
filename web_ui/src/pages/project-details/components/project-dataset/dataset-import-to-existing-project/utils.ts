// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { uniq } from 'lodash-es';

export const KEYPOINT_DUPLICATED_LABELS = 'Duplicate labels are not allow in keypoint detection projects.';

export const hasDuplicatedValues = (data: Record<string, string>) => {
    const values = Object.values(data);
    return uniq(values).length !== values.length;
};
