// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { parseAnnotationProposal, type AnnotationTarget } from './annotation-tools';

const target = (taskType: AnnotationTarget['taskType']): AnnotationTarget => ({
    key: 'media-1',
    width: 100,
    height: 100,
    taskType,
    exclusiveLabels: true,
    labels: [{ id: 'label-1', name: 'Object', color: '#ffffff' }],
    source: { id: 'media-1', name: 'image.jpg', url: '/image.jpg' },
    apply: vi.fn(),
});

const proposal = (annotation: Record<string, unknown>) => ({
    media_key: 'media-1',
    annotations: [{ label_ids: ['label-1'], ...annotation }],
});

it('clips a partially outside detection box to the image', () => {
    const [annotation] = parseAnnotationProposal(
        proposal({ x: -10, y: 90, width: 30, height: 30 }),
        target('detection')
    );

    expect(annotation.shape).toEqual({ type: 'rectangle', x: 0, y: 90, width: 20, height: 10 });
});

it('rejects a detection box with no visible area', () => {
    expect(() =>
        parseAnnotationProposal(proposal({ x: 110, y: 10, width: 20, height: 20 }), target('detection'))
    ).toThrow('A box is outside the original image.');
});

it('clips a partially outside segmentation polygon to the image', () => {
    const [annotation] = parseAnnotationProposal(
        proposal({
            points: [
                { x: -10, y: 20 },
                { x: 20, y: 20 },
                { x: 20, y: 120 },
                { x: -10, y: 120 },
            ],
        }),
        target('instance_segmentation')
    );

    expect(annotation.shape).toEqual({
        type: 'polygon',
        points: [
            { x: 0, y: 100 },
            { x: 0, y: 20 },
            { x: 20, y: 20 },
            { x: 20, y: 100 },
        ],
    });
});

it('rejects a segmentation polygon with no visible area', () => {
    expect(() =>
        parseAnnotationProposal(
            proposal({
                points: [
                    { x: 110, y: 10 },
                    { x: 120, y: 10 },
                    { x: 120, y: 20 },
                ],
            }),
            target('instance_segmentation')
        )
    ).toThrow('A polygon is outside the original image.');
});
