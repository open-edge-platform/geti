// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
