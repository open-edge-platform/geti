// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotatedVideoFrame } from '@/api/types';

type AnnotationGroup = Pick<AnnotatedVideoFrame['annotation_data'], 'annotations'>;

export const getAnnotationCounts = (groups: AnnotationGroup[]) => {
    let annotationCount = 0;
    const labelIds = new Set<string>();

    // Count No object/No label as a distinct category, as DatasetLabelsChart does.
    // Unlike this count, MediaFilterLabels only lists project labels, excluding the empty label.
    for (const { annotations } of groups) {
        annotationCount += annotations.length;
        for (const annotation of annotations) {
            for (const label of annotation.labels) {
                labelIds.add(label.id);
            }
        }
    }

    return { annotationCount, labelCount: labelIds.size };
};
