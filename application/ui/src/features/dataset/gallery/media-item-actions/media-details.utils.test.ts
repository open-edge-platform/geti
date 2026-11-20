// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { EMPTY_LABEL_ID } from '../../../../shared/labels';
import { getAnnotationCounts } from './media-details.utils';

const annotationsFor = (...labelIds: string[]) =>
    labelIds.map((id) => ({ shape: { type: 'full_image' as const }, labels: [{ id }] }));

describe('getAnnotationCounts', () => {
    it('counts normalized image annotations and deduplicates labels, including No object', () => {
        expect(getAnnotationCounts([])).toEqual({ annotationCount: 0, labelCount: 0 });
        expect(getAnnotationCounts([{ annotations: annotationsFor(EMPTY_LABEL_ID) }])).toEqual({
            annotationCount: 1,
            labelCount: 1,
        });
        expect(getAnnotationCounts([{ annotations: annotationsFor('label-1', 'label-1', 'label-2') }])).toEqual({
            annotationCount: 3,
            labelCount: 2,
        });
    });

    it('aggregates normalized video annotations and deduplicates labels, including No object', () => {
        expect(
            getAnnotationCounts([
                { annotations: annotationsFor('label-1', 'label-1') },
                { annotations: annotationsFor(EMPTY_LABEL_ID) },
                { annotations: annotationsFor(EMPTY_LABEL_ID) },
                { annotations: [] },
                { annotations: annotationsFor('label-1', 'label-2') },
            ])
        ).toEqual({ annotationCount: 6, labelCount: 3 });
    });
});
