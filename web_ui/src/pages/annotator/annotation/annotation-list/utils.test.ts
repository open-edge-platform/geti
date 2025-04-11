// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
