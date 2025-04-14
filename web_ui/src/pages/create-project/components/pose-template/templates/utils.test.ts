// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { formatTemplate } from './utils';

describe('formatTemplate', () => {
    const mockRoi = { x: 0, y: 0, width: 100, height: 100 };

    it('maps and denormalize points', () => {
        const mockStructure = {
            points: [
                { label: 'point1', x: 0.1, y: 0.2 },
                { label: 'point2', x: 0.3, y: 0.4 },
            ],
            edges: [{ from: 'point1', to: 'point2' }],
        };

        const result = formatTemplate(mockStructure, mockRoi);
        const [point1, point2] = result.points;

        expect(result.edges[0].from).toMatchObject(point1);
        expect(result.edges[0].to).toMatchObject(point2);

        expect(result.points).toEqual([
            {
                x: 10,
                y: 20,
                isVisible: true,
                label: expect.objectContaining({ name: 'point1' }),
            },
            {
                x: 30,
                y: 40,
                isVisible: true,
                label: expect.objectContaining({ name: 'point2' }),
            },
        ]);
    });

    describe('remove invalid edges', () => {
        it('invalid point', () => {
            const mockStructure = {
                points: [
                    { label: 'point1', x: 0.1, y: 0.2 },
                    { label: 'point2', x: 0.3, y: 0.4 },
                ],
                edges: [{ from: 'point3', to: 'point2' }],
            };

            const result = formatTemplate(mockStructure, mockRoi);

            expect(result.edges).toHaveLength(0);
        });

        it('edges with identical from and to points', () => {
            const mockStructure = {
                points: [{ label: 'point1', x: 0.1, y: 0.2 }],
                edges: [{ from: 'point1', to: 'point1' }],
            };

            const result = formatTemplate(mockStructure, mockRoi);

            expect(result.edges).toHaveLength(0);
        });
    });

    it('should return an empty points array if structure has no points', () => {
        const mockStructure = { points: [], edges: [] };

        const result = formatTemplate(mockStructure, mockRoi);

        expect(result.points).toHaveLength(0);
    });
});
