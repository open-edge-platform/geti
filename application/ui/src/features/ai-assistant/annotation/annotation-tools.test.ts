// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it, vi } from 'vitest';

import { annotationTool, parseAnnotationProposal, type AnnotationTarget } from './annotation-tools';

const target: AnnotationTarget = {
    key: 'project/image',
    width: 2000,
    height: 1500,
    taskType: 'detection',
    exclusiveLabels: true,
    labels: [
        { id: 'cat', name: 'Cat', color: '#ff0000' },
        { id: 'dog', name: 'Dog', color: '#00ff00' },
    ],
    source: { id: 'image', name: 'Image', url: '/image.png' },
    apply: vi.fn(),
};
const box = { label_ids: ['cat'], x: 1200, y: 1000, width: 300, height: 250 };
const args = (annotations: unknown[]) => ({ media_key: target.key, annotations });

describe('ChatGPT annotation proposals', () => {
    it('preserves original image coordinates even beyond the preview resolution', () => {
        const [annotation] = parseAnnotationProposal(args([box]), target);
        expect(annotation.shape).toEqual({ type: 'rectangle', x: 1200, y: 1000, width: 300, height: 250 });
        expect(annotation.labels).toEqual([{ id: 'cat' }]);
        expect(target.apply).not.toHaveBeenCalled();
    });
    it.each([
        { ...box, x: -1 },
        { ...box, width: 0 },
        { ...box, width: 3000 },
        { ...box, y: Infinity },
        { ...box, x: '12' },
        { ...box, label_ids: ['invented'] },
        { ...box, label_ids: ['cat', 'dog'] },
        { ...box, label_ids: [] },
    ])('rejects invalid geometry or labels: %j', (invalid) => {
        expect(() => parseAnnotationProposal(args([box, invalid]), target)).toThrow();
    });
    it('rejects a response for a different image', () => {
        expect(() => parseAnnotationProposal({ ...args([box]), media_key: 'other' }, target)).toThrow('image changed');
    });
    it('creates a polygon and rejects degenerate geometry', () => {
        const segmentation = { ...target, taskType: 'instance_segmentation' as const };
        const points = [
            { x: 1, y: 1 },
            { x: 100, y: 1 },
            { x: 100, y: 200 },
        ];
        expect(parseAnnotationProposal(args([{ label_ids: ['cat'], points }]), segmentation)[0].shape).toEqual({
            type: 'polygon',
            points,
        });
        expect(() =>
            parseAnnotationProposal(
                args([
                    {
                        label_ids: ['cat'],
                        points: [
                            { x: 1, y: 1 },
                            { x: 2, y: 2 },
                            { x: 3, y: 3 },
                        ],
                    },
                ]),
                segmentation
            )
        ).toThrow('zero area');
    });
    it('supports multilabel and exclusive image classification', () => {
        const classification = { ...target, taskType: 'classification' as const, exclusiveLabels: false };
        const [annotation] = parseAnnotationProposal(args([{ label_ids: ['cat', 'dog'] }]), classification);
        expect(annotation.shape).toEqual({ type: 'full_image' });
        expect(annotation.labels).toHaveLength(2);
        expect(() =>
            parseAnnotationProposal(args([{ label_ids: ['cat', 'dog'] }]), { ...classification, exclusiveLabels: true })
        ).toThrow('exclusive');
    });
    it('allows an empty proposal without changing existing annotations', () => {
        expect(parseAnnotationProposal(args([]), target)).toEqual([]);
        expect(target.apply).not.toHaveBeenCalled();
    });
    it('bounds response size', () => {
        expect(() => parseAnnotationProposal(args(Array.from({ length: 101 }, () => box)), target)).toThrow('maximum');
    });
    it('offers only geometry matching the project task', () => {
        expect(JSON.stringify(annotationTool(target))).toContain('width');
        expect(JSON.stringify(annotationTool({ ...target, taskType: 'classification' }))).not.toContain('"points"');
        expect(JSON.stringify(annotationTool({ ...target, taskType: 'classification' }))).not.toContain('"width"');
    });
});
