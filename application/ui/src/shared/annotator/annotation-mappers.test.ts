// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getMockedShape } from 'mocks/mock-annotation';
import { getMockedAnnotationLabelRef } from 'mocks/mock-labels';

import type { AnnotationDTO } from '@/api/types';
import { mapLocalAnnotationsToServer, mapServerAnnotationsToLocal } from './annotation-mappers';

describe('mapServerAnnotationsToLocal', () => {
    it('maps a label with no confidence score to a ref without a probability', () => {
        const dto: AnnotationDTO[] = [
            { labels: [{ id: 'label-1' }], shape: getMockedShape({ type: 'rectangle' }), confidences: null },
        ];

        const [annotation] = mapServerAnnotationsToLocal(dto);

        expect(annotation.labels).toEqual([{ id: 'label-1' }]);
        expect(annotation.labels[0]).not.toHaveProperty('probability');
    });

    it('maps a label with a confidence score to a ref with a matching probability', () => {
        const dto: AnnotationDTO[] = [
            { labels: [{ id: 'label-1' }], shape: getMockedShape({ type: 'rectangle' }), confidences: [0.87] },
        ];

        const [annotation] = mapServerAnnotationsToLocal(dto);

        expect(annotation.labels).toEqual([{ id: 'label-1', probability: 0.87 }]);
    });
});

describe('mapLocalAnnotationsToServer', () => {
    it('maps confidences to null when no label has a probability', () => {
        const annotation = {
            id: 'annotation-1',
            shape: getMockedShape({ type: 'rectangle' }),
            labels: [getMockedAnnotationLabelRef({ id: 'label-1' })],
        };

        const [result] = mapLocalAnnotationsToServer([annotation]);

        expect(result).toHaveProperty('confidences', null);
    });

    it('maps confidences to an array of probabilities, in label order, when present', () => {
        const annotation = {
            id: 'annotation-1',
            shape: getMockedShape({ type: 'rectangle' }),
            labels: [
                getMockedAnnotationLabelRef({ id: 'label-1', probability: 0.6 }),
                getMockedAnnotationLabelRef({ id: 'label-2', probability: 0.4 }),
            ],
        };

        const [result] = mapLocalAnnotationsToServer([annotation]);

        expect(result.confidences).toEqual([0.6, 0.4]);
    });

    it('strips labels that are not in the provided valid id set', () => {
        const annotation = {
            id: 'annotation-1',
            shape: getMockedShape({ type: 'rectangle' }),
            labels: [
                getMockedAnnotationLabelRef({ id: 'label-1' }),
                getMockedAnnotationLabelRef({ id: 'deleted-label' }),
            ],
        };

        const [result] = mapLocalAnnotationsToServer([annotation], new Set(['label-1']));

        expect(result.labels).toEqual([{ id: 'label-1' }]);
    });

    it('keeps all labels when no valid id set is provided', () => {
        const annotation = {
            id: 'annotation-1',
            shape: getMockedShape({ type: 'rectangle' }),
            labels: [getMockedAnnotationLabelRef({ id: 'label-1' })],
        };

        const [result] = mapLocalAnnotationsToServer([annotation]);

        expect(result.labels).toEqual([{ id: 'label-1' }]);
    });
});

describe('round trip: mapLocalAnnotationsToServer(mapServerAnnotationsToLocal(dto))', () => {
    it('is deep-equal to a plain (non-prediction) server annotation, confidences included', () => {
        // This is the exact shape the backend returns for a human annotation with no confidence
        // scores: `confidences` is present and `null`, never omitted.
        const dto: AnnotationDTO[] = [
            { labels: [{ id: 'label-1' }], shape: getMockedShape({ type: 'rectangle' }), confidences: null },
        ];

        const roundTripped = mapLocalAnnotationsToServer(mapServerAnnotationsToLocal(dto));

        expect(roundTripped).toEqual(dto);
    });

    it('is deep-equal to a prediction-style server annotation, confidences included', () => {
        const dto: AnnotationDTO[] = [
            { labels: [{ id: 'label-1' }], shape: getMockedShape({ type: 'rectangle' }), confidences: [0.95] },
        ];

        const roundTripped = mapLocalAnnotationsToServer(mapServerAnnotationsToLocal(dto));

        expect(roundTripped).toEqual(dto);
    });
});
