// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
