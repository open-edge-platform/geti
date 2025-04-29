// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { RITMPoint } from './ritm-tool.interface';
import {
    buildDynamicBox,
    createBoxOfMaxSize,
    encapsulatePoints,
    encapsulateRegions,
    scaleRegionOfInterest,
} from './util';

const r = (x: number, y: number, width: number, height: number): RegionOfInterest => {
    return { x, y, width, height };
};

const p = (x: number, y: number, positive = true): RITMPoint => {
    return { x, y, positive };
};

describe('util', () => {
    describe('createBoxOfMaxSize', () => {
        describe('bigger ROIs', () => {
            const testData: [[number, number], number, [number, number]][] = [
                [[200, 200], 100, [100, 100]],
                [[100, 200], 100, [50, 100]],
                [[300, 200], 100, [100, 66]],
            ];

            test.each(testData)(
                'reduces the ROI %p to max size %p and get %p',
                ([width, height], maxSize, [expectedWidth, expectedHeight]) => {
                    const subject = createBoxOfMaxSize({ width, height }, maxSize);
                    expect(subject).toEqual({ width: expectedWidth, height: expectedHeight });
                }
            );
        });
    });

    describe('scaleRegionOfInterest', () => {
        const testData: [RegionOfInterest, number, RegionOfInterest][] = [
            [r(50, 50, 100, 100), 1, r(50, 50, 100, 100)],
            [r(50, 50, 100, 100), 1.1, r(45, 45, 110, 110)],
            [r(50, 50, 100, 100), 0.9, r(55, 55, 90, 90)],
        ];

        test.each(testData)('takes ROI %p and adds factor %p to get %p', (region, factor, expectedRegion) => {
            const subject = scaleRegionOfInterest(region, factor);
            expect(subject.x).toBeCloseTo(expectedRegion.x, 3);
            expect(subject.y).toBeCloseTo(expectedRegion.y, 3);
            expect(subject.width).toBeCloseTo(expectedRegion.width, 3);
            expect(subject.height).toBeCloseTo(expectedRegion.height, 3);
        });
    });

    describe('encapsulateRegions', () => {
        const testData: [RegionOfInterest, RegionOfInterest, RegionOfInterest][] = [
            [r(50, 50, 50, 50), r(100, 100, 50, 50), r(50, 50, 100, 100)],
            [r(200, 10, 5, 5), r(10, 100, 100, 100), r(10, 10, 195, 190)],
        ];

        test.each(testData)('takes ROI %p and %p and encapsulates to get %p', (regionA, regionB, expectedRegion) => {
            const subject = encapsulateRegions([regionA, regionB]);
            expect(subject).toEqual(expectedRegion);
        });
    });

    describe('encapsulatePoints', () => {
        const testData: [RITMPoint, RITMPoint, number, RegionOfInterest][] = [
            [p(50, 50), p(50, 50), 0, r(50, 50, 0, 0)],
            [p(50, 50), p(50, 50), 10, r(40, 40, 20, 20)],
            [p(200, 10), p(10, 100), 0, r(10, 10, 190, 90)],
        ];

        test.each(testData)(
            'takes points %p and %p adds margin %p to get %p',
            (pointA, pointB, margin, expectedRegion) => {
                const subject = encapsulatePoints([pointA, pointB], margin);
                expect(subject).toEqual(expectedRegion);
            }
        );

        it('takes as many points as you want', () => {
            const points = [p(10, 10), p(10, 30), p(100, 100), p(200, 100)];
            expect(encapsulatePoints(points, 0)).toEqual(r(10, 10, 190, 90));
        });
    });

    describe('buildDynamicBox', () => {
        it('takes current points, box, margin and image size to build a region of interest', () => {
            const points = [p(10, 30), p(40, 100), p(20, 100)];
            const currentPosition = { x: 10, y: 10 };
            const box = r(50, 50, 100, 100);
            const image = { x: 0, y: 0, width: 100, height: 100 };
            const margin = 5;
            const subject = buildDynamicBox(points, currentPosition, box, image, margin);
            expect(subject).toEqual(r(5, 5, 95, 95));
        });
    });
});
