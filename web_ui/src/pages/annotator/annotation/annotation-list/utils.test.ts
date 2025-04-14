// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { reorder } from './utils';

describe('Annotations list utils', () => {
    it('reorder', () => {
        const mockAnnotations = [
            getMockedAnnotation({ id: 'test-annotation-1' }),
            getMockedAnnotation({ id: 'test-annotation-2' }),
            getMockedAnnotation({ id: 'test-annotation-3' }),
            getMockedAnnotation({ id: 'test-annotation-4' }),
        ];

        expect(reorder(mockAnnotations, 1, 3)).toEqual([
            { ...mockAnnotations[1], zIndex: 0 },
            { ...mockAnnotations[3], zIndex: 1 },
            { ...mockAnnotations[2], zIndex: 2 },
            { ...mockAnnotations[0], zIndex: 3 },
        ]);
    });
});
