// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { toggleVisibility, updatePoint } from './util';

describe('edit-keypoint utils', () => {
    it('update the point and deselect all other items', () => {
        const index = 1;
        const newCoordinates = { x: 2, y: 2 };
        const mockedKeypointNode = getMockedKeypointNode({});
        const defaultKeypointNode = getMockedKeypointNode({});

        const result = updatePoint(
            [defaultKeypointNode, mockedKeypointNode, defaultKeypointNode],
            index,
            newCoordinates
        );

        expect(result).toEqual([
            { ...defaultKeypointNode },
            { ...mockedKeypointNode, ...newCoordinates },
            { ...defaultKeypointNode },
        ]);
    });

    describe('toggleVisibility', () => {
        it('sets visibility to true', () => {
            const mockedKeypointNode = getMockedKeypointNode({ isVisible: false });
            const defaultKeypointNode = getMockedKeypointNode({});

            const result = toggleVisibility([mockedKeypointNode, defaultKeypointNode], 0);

            expect(result).toEqual([{ ...defaultKeypointNode }, { ...mockedKeypointNode, isVisible: true }]);
        });

        it('sets visibility to false', () => {
            const mockedKeypointNode = getMockedKeypointNode({ isVisible: true });
            const defaultKeypointNode = getMockedKeypointNode({});

            const result = toggleVisibility([defaultKeypointNode, mockedKeypointNode], 1);

            expect(result).toEqual([{ ...defaultKeypointNode }, { ...mockedKeypointNode, isVisible: false }]);
        });
    });
});
