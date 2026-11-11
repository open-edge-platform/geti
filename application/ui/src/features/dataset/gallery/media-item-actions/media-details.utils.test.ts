// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { EMPTY_LABEL_ID } from '../../../../shared/labels';
import { getAnnotationCounts } from './media-details.utils';

const annotationsFor = (...labelIds: string[]) =>
    labelIds.map((id) => ({ shape: { type: 'full_image' as const }, labels: [{ id }] }));

describe('getAnnotationCounts', () => {
    it('counts normalized image annotations and deduplicates labels, including No object', () => {
        expect(getAnnotationCounts([])).toEqual({ annotationCount: 0, labelCount: 0 });
        expect(getAnnotationCounts([{ annotations: annotationsFor(EMPTY_LABEL_ID), user_reviewed: true }])).toEqual({
            annotationCount: 1,
            labelCount: 1,
        });
        expect(
            getAnnotationCounts([{ annotations: annotationsFor('label-1', 'label-1', 'label-2'), user_reviewed: true }])
        ).toEqual({ annotationCount: 3, labelCount: 2 });
    });

    it('aggregates video annotations, counting reviewed empty frames but not unreviewed ones', () => {
        expect(
            getAnnotationCounts([
                { annotations: annotationsFor('label-1', 'label-1'), user_reviewed: true },
                { annotations: [], user_reviewed: true },
                { annotations: [], user_reviewed: true },
                { annotations: [], user_reviewed: false },
                { annotations: annotationsFor('label-1', 'label-2'), user_reviewed: true },
            ])
        ).toEqual({ annotationCount: 6, labelCount: 3 });
    });
});
