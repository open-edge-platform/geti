// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotatedVideoFrame } from '@/api/types';

import { EMPTY_LABEL_ID } from '../../../../shared/labels';

type AnnotationGroup = Pick<AnnotatedVideoFrame['annotation_data'], 'annotations' | 'user_reviewed'>;

export const getAnnotationCounts = (groups: AnnotationGroup[]) => {
    let annotationCount = 0;
    const labelIds = new Set<string>();

    // Count No object/No label as a distinct category, as DatasetLabelsChart does.
    // Unlike this count, MediaFilterLabels only lists project labels, excluding the empty label.
    // Image queries normalize empty annotations to EMPTY_LABEL_ID; video frames need it added explicitly.
    for (const { annotations, user_reviewed } of groups) {
        annotationCount += annotations.length || (user_reviewed ? 1 : 0);
        for (const annotation of annotations) {
            for (const label of annotation.labels) {
                labelIds.add(label.id);
            }
        }
        if (user_reviewed && annotations.length === 0) {
            labelIds.add(EMPTY_LABEL_ID);
        }
    }

    return { annotationCount, labelCount: labelIds.size };
};
