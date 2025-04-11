// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { LabelItemEditionState, LabelItemType } from '../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { EMPTY_LABEL_MESSAGE, MIN_POINTS_MESSAGE } from '../../utils';
import {
    createRoi,
    getDefaultLabelStructure,
    getDuplicateLabelNames,
    getLabelFromPoint,
    getProjectTypeMetadata,
    getValidationError,
    isDifferentLabel,
    isEdgeConnectingPoints,
    isEqualLabel,
    isMatchingEdge,
    isPointInEdge,
    rgbToHex,
    updateWithLatestPoints,
} from './util';

describe('post-template utils', () => {
    describe('isEqualLabel', () => {
        const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
        const pointC = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });

        it('return true for points with the same label', () => {
            expect(isEqualLabel(pointA)(pointC)).toBe(true);
        });

        it('return false for points with different labels', () => {
            expect(isEqualLabel(pointA)(pointB)).toBe(false);
        });
    });

    describe('isDifferentLabel', () => {
        const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
        const pointC = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });

        it('return true for points with different labels', () => {
            expect(isDifferentLabel(pointA)(pointB)).toBe(true);
        });

        it('return false for points with the same label', () => {
            expect(isDifferentLabel(pointA)(pointC)).toBe(false);
        });
    });

    it('getDefaultLabelStructure', () => {
        const name = 'test name';

        expect(getDefaultLabelStructure(name)).toEqual(
            expect.objectContaining({
                name,
                group: '',
                parentLabelId: null,
                relation: LabelsRelationType.SINGLE_SELECTION,
            })
        );
    });

    describe('rgbToHex', () => {
        it('convert RGB values to hex correctly', () => {
            expect(rgbToHex(255, 0, 0)).toBe('#ff0000');
            expect(rgbToHex(0, 255, 0)).toBe('#00ff00');
            expect(rgbToHex(0, 0, 255)).toBe('#0000ff');
            expect(rgbToHex(255, 255, 255)).toBe('#ffffff');
            expect(rgbToHex(0, 0, 0)).toBe('#000000');
        });

        it('pad single digit hex values with leading zeros', () => {
            expect(rgbToHex(15, 15, 15)).toBe('#0f0f0f');
            expect(rgbToHex(16, 16, 16)).toBe('#101010');
        });
    });

    describe('getDuplicateLabelNames', () => {
        const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
        const pointC = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });

        it('return an empty array if there are no duplicate labels', () => {
            expect(getDuplicateLabelNames([pointA, pointB])).toEqual([]);
        });

        it('return an array with duplicate label names', () => {
            expect(getDuplicateLabelNames([pointA, pointC])).toEqual(['label A']);
        });

        it('return an array with multiple duplicate label names', () => {
            const pointD = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
            expect(getDuplicateLabelNames([pointA, pointB, pointC, pointD])).toEqual(['label A', 'label B']);
        });
    });

    describe('getValidationError', () => {
        const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
        const pointC = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointD = getMockedKeypointNode({ label: getMockedLabel({ id: 'label C', name: '' }) });
        const pointF = getMockedKeypointNode({ label: getMockedLabel({ id: 'label F', name: '' }) });

        it('returns MIN_POINTS_MESSAGE if no points are provided', () => {
            expect(getValidationError([])).toBe(MIN_POINTS_MESSAGE);
        });

        it('returns EMPTY_LABEL_MESSAGE if there are empty labels', () => {
            expect(getValidationError([pointA, pointD])).toBe(EMPTY_LABEL_MESSAGE);
            expect(getValidationError([pointC, pointF])).toBe(EMPTY_LABEL_MESSAGE);
        });

        it('returns an error message if there are duplicate labels', () => {
            expect(getValidationError([pointA, pointC])).toBe(
                'Label names must be unique, label "label A" is duplicated'
            );
        });

        it('returns an error message if there are multiple duplicate labels', () => {
            const pointE = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
            expect(getValidationError([pointA, pointB, pointC, pointE])).toBe(
                'Label names must be unique, labels "label A" ,"label B" are duplicated'
            );
        });

        it('returns undefined if there are no duplicate labels and no empty labels', () => {
            expect(getValidationError([pointA, pointB])).toBeUndefined();
        });
    });
    describe('getLabelFromPoint', () => {
        it('format KeypointNode to a LabelTreeItem', () => {
            const point = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
            const labelTreeItem = getLabelFromPoint(point);

            expect(labelTreeItem).toEqual(
                expect.objectContaining({
                    ...point.label,
                    open: false,
                    inEditMode: false,
                    children: [],
                    type: LabelItemType.LABEL,
                    state: LabelItemEditionState.IDLE,
                    relation: LabelsRelationType.SINGLE_SELECTION,
                })
            );
        });
    });

    it('createRoi', () => {
        expect(createRoi(10, 20)).toEqual({ x: 0, y: 0, width: 10, height: 20 });
        expect(createRoi(undefined, undefined)).toEqual({ x: 0, y: 0, width: 0, height: 0 });
    });

    describe('getProjectTypeMetadata', () => {
        it('return TaskMetadata with normalized points', () => {
            const pointA = getMockedKeypointNode({
                x: 50,
                y: 50,
                label: getMockedLabel({ id: 'label A', name: 'label A' }),
            });
            const pointB = getMockedKeypointNode({
                x: 100,
                y: 100,
                label: getMockedLabel({ id: 'label B', name: 'label B' }),
            });

            const edge = { id: 'edge1', from: pointA, to: pointB };
            const roi = { x: 0, y: 0, width: 200, height: 200 };

            expect(getProjectTypeMetadata([pointA, pointB], [edge], roi)).toEqual({
                domain: DOMAIN.KEYPOINT_DETECTION,
                relation: LabelsRelationType.SINGLE_SELECTION,
                labels: [getLabelFromPoint(pointA), getLabelFromPoint(pointB)],
                keypointStructure: {
                    edges: [{ nodes: ['label A', 'label B'] }],
                    positions: [
                        { label: 'label A', x: 0.25, y: 0.25 },
                        { label: 'label B', x: 0.5, y: 0.5 },
                    ],
                },
            });
        });
    });

    describe('isPointInEdge', () => {
        const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
        const edge = { id: 'edge1', from: pointA, to: pointB };

        it('the point is part of the edge', () => {
            expect(isPointInEdge(pointA)(edge)).toBe(true);
            expect(isPointInEdge(pointB)(edge)).toBe(true);
        });

        it('the point is not part of the edge', () => {
            const pointC = getMockedKeypointNode({ label: getMockedLabel({ id: 'label C', name: 'label C' }) });
            expect(isPointInEdge(pointC)(edge)).toBe(false);
        });
    });

    describe('isEdgeConnectingPoints', () => {
        const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
        const edge = { id: 'edge1', from: pointA, to: pointB };

        it('both points are part of the edge', () => {
            expect(isEdgeConnectingPoints(pointA, pointB)(edge)).toBe(true);
        });

        it('one of the points is not part of the edge', () => {
            const pointC = getMockedKeypointNode({ label: getMockedLabel({ id: 'label C', name: 'label C' }) });
            expect(isEdgeConnectingPoints(pointA, pointC)(edge)).toBe(false);
        });
    });

    describe('updateWithLatestPoints', () => {
        it('update edge with latest points', () => {
            const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: '1', name: '1' }) });
            const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: '2', name: '2' }) });

            expect(updateWithLatestPoints([pointA])({ id: 'edge1', from: pointA, to: pointB })).toEqual({
                id: 'edge1',
                from: pointA,
                to: undefined,
            });
        });
    });
    describe('isMatchingEdge', () => {
        const pointA = getMockedKeypointNode({ label: getMockedLabel({ id: 'label A', name: 'label A' }) });
        const pointB = getMockedKeypointNode({ label: getMockedLabel({ id: 'label B', name: 'label B' }) });
        const pointC = getMockedKeypointNode({ label: getMockedLabel({ id: 'label C', name: 'label C' }) });

        const edgeAB = { id: 'edge1', from: pointA, to: pointB };

        it('edge matches the given points', () => {
            expect(isMatchingEdge(pointA, pointB)(edgeAB)).toBe(true);
        });

        it('points are swapped', () => {
            expect(isMatchingEdge(pointB, pointA)(edgeAB)).toBe(false);
        });

        it('edge does not match the given points', () => {
            expect(isMatchingEdge(pointA, pointC)(edgeAB)).toBe(false);
            expect(isMatchingEdge(pointC, pointB)(edgeAB)).toBe(false);
        });
    });
});
