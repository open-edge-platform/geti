// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { type WatershedPolygon } from '@geti/smart-tools';

import { Label, LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { getImageData } from '../../../../shared/canvas-utils';
import { getMaxSensitivityForImage, mapPolygonsToWatershedPolygons } from './utils';

describe('utils', () => {
    describe('getMaxSensitivityForImage', () => {
        it('returns at least one sensitivity', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(0, 0)))).toEqual(1);
        });

        it('returns sensitivities available based on image', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(2000, 2000)))).toEqual(4);
        });

        it('uses the highest side of the image', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(2000, 0)))).toEqual(4);
            expect(getMaxSensitivityForImage(getImageData(new Image(0, 2000)))).toEqual(4);
        });

        it('very high image returns the last sensitivity', () => {
            expect(getMaxSensitivityForImage(getImageData(new Image(6000, 0)))).toEqual(5);
        });
    });

    describe('mapPolygonsToWatershedPolygons', () => {
        const label1: Label = {
            id: 'label-1',
            name: 'Label 1',
            color: '#ff0000',
            parentLabelId: '',
            group: '',
            behaviour: LABEL_BEHAVIOUR.LOCAL,
            hotkey: '',
            isEmpty: false,
        };
        const label2: Label = {
            id: 'label-2',
            name: 'Label 2',
            color: '#00ff00',
            parentLabelId: '',
            group: '',
            behaviour: LABEL_BEHAVIOUR.LOCAL,
            hotkey: '',
            isEmpty: false,
        };

        const polygon1: WatershedPolygon = {
            id: 1,
            points: [
                { x: 0, y: 0 },
                { x: 1, y: 1 },
                { x: 2, y: 2 },
            ],
            label: { id: 'label-1' },
        };
        const polygon2: WatershedPolygon = {
            id: 2,
            points: [
                { x: 3, y: 3 },
                { x: 4, y: 4 },
                { x: 5, y: 5 },
            ],
            label: { id: 'label-2' },
        };

        it('returns empty array if input is empty', () => {
            expect(mapPolygonsToWatershedPolygons([], [label1, label2])).toEqual([]);
        });

        it('maps polygons to include full label info', () => {
            const result = mapPolygonsToWatershedPolygons([polygon1, polygon2], [label1, label2]);
            expect(result).toHaveLength(2);
            expect(result[0].label).toEqual(label1);
            expect(result[1].label).toEqual(label2);
            expect(result[0].points).toEqual(polygon1.points);
            expect(result[1].points).toEqual(polygon2.points);
        });

        it('assigns unknown label if label not found', () => {
            const polygonWithUnknownLabel: WatershedPolygon = {
                id: 123,
                points: [
                    { x: 6, y: 6 },
                    { x: 7, y: 7 },
                ],
                label: { id: 'unknown-label' },
            };
            const result = mapPolygonsToWatershedPolygons([polygonWithUnknownLabel], [label1]);
            expect(result[0].label.id).toBe('unknown-label');
            expect(result[0].label.name).toBe('Unknown');
            expect(result[0].label.color).toBe('#000000');
        });
    });
});
