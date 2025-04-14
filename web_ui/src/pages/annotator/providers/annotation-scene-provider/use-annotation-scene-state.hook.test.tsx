// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, renderHook } from '@testing-library/react';

import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { useAnnotationSceneState } from './use-annotation-scene-state.hook';

const mockLabels = getMockedLabels(3);
const mockAnnotations = Array.from({ length: 4 }, (_, index) =>
    getMockedAnnotation({ id: `test-id-${index}`, zIndex: index })
);

describe('useAnnotationSceneState', () => {
    it('removes annotations and reorder the "zindex" with consecutive order', () => {
        const { result } = renderHook(() => useAnnotationSceneState(mockAnnotations, mockLabels));
        const toDelete = [mockAnnotations[0], mockAnnotations[2]];
        act(() => {
            result.current.removeAnnotations(toDelete);
        });

        expect(result.current.annotations).toEqual([
            { ...mockAnnotations[1], zIndex: 0 },
            { ...mockAnnotations[3], zIndex: 1 },
        ]);
    });
});
