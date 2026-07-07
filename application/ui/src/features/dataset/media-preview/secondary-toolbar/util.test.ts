// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getMockedAnnotation } from 'mocks/mock-annotation';
import { getMockedAnnotationLabelRef, getMockedLabel } from 'mocks/mock-labels';
import { describe, expect, it } from 'vitest';

import { getIsSubmitDisabled, toggleLabel } from './util';

describe('secondary toolbar utils', () => {
    describe('getIsSubmitDisabled', () => {
        const defaultParams = {
            mode: 'annotation' as const,
            canSubmit: false,
            hasInvalidAnnotation: false,
            hasSubsetChanged: false,
            isSaving: false,
            isLoadingPredictions: false,
        };

        it('annotation mode: enabled when there is a new annotation', () => {
            const result = getIsSubmitDisabled({ ...defaultParams, canSubmit: true, hasSubsetChanged: false });

            expect(result).toBe(false);
        });

        it('annotation mode: enabled when annotations are unchanged but subset changed', () => {
            const result = getIsSubmitDisabled({ ...defaultParams, canSubmit: false, hasSubsetChanged: true });

            expect(result).toBe(false);
        });

        it('annotation mode: disabled when annotations and subset are both unchanged', () => {
            const result = getIsSubmitDisabled({ ...defaultParams, canSubmit: false, hasSubsetChanged: false });

            expect(result).toBe(true);
        });

        it('annotation mode: disabled when annotation is invalid, even if subset changed', () => {
            const result = getIsSubmitDisabled({
                ...defaultParams,
                canSubmit: false,
                hasInvalidAnnotation: true,
                hasSubsetChanged: true,
            });

            expect(result).toBe(true);
        });

        it('annotation mode: disabled while saving, regardless of other flags', () => {
            const result = getIsSubmitDisabled({
                ...defaultParams,
                canSubmit: true,
                hasSubsetChanged: true,
                isSaving: true,
            });

            expect(result).toBe(true);
        });

        it('prediction mode: enabled when a prediction is present and subset is unchanged', () => {
            const result = getIsSubmitDisabled({
                ...defaultParams,
                mode: 'prediction',
                canSubmit: true,
                hasSubsetChanged: false,
            });

            expect(result).toBe(false);
        });

        it('prediction mode: enabled when a prediction is present and subset changed', () => {
            const result = getIsSubmitDisabled({
                ...defaultParams,
                mode: 'prediction',
                canSubmit: true,
                hasSubsetChanged: true,
            });

            expect(result).toBe(false);
        });

        it('prediction mode: disabled when there is no prediction, even if subset changed', () => {
            const result = getIsSubmitDisabled({
                ...defaultParams,
                mode: 'prediction',
                canSubmit: false,
                hasSubsetChanged: true,
            });

            expect(result).toBe(true);
        });

        it('prediction mode: disabled when there is no prediction and subset is unchanged', () => {
            const result = getIsSubmitDisabled({
                ...defaultParams,
                mode: 'prediction',
                canSubmit: false,
                hasSubsetChanged: false,
            });

            expect(result).toBe(true);
        });

        it('prediction mode: disabled while loading predictions, regardless of other flags', () => {
            const result = getIsSubmitDisabled({
                ...defaultParams,
                mode: 'prediction',
                canSubmit: true,
                isLoadingPredictions: true,
            });

            expect(result).toBe(true);
        });
    });

    describe('toggleLabel', () => {
        const mockLabel1 = getMockedLabel({ id: 'label-1', name: 'Label 1' });
        const mockLabel2 = getMockedLabel({ id: 'label-2', name: 'Label 2' });
        const mockLabel3 = getMockedLabel({ id: 'label-3', name: 'Label 3' });

        it('add label when it does not exist in annotation', () => {
            const annotation = getMockedAnnotation({
                labels: [
                    getMockedAnnotationLabelRef({ id: 'label-1' }),
                    getMockedAnnotationLabelRef({ id: 'label-2' }),
                ],
            });

            const result = toggleLabel(mockLabel3, annotation.labels);

            expect(result).toEqual([{ id: 'label-1' }, { id: 'label-2' }, { id: 'label-3' }]);
        });

        it('remove label when it exists in annotation', () => {
            const annotation = getMockedAnnotation({
                labels: [
                    getMockedAnnotationLabelRef({ id: 'label-1' }),
                    getMockedAnnotationLabelRef({ id: 'label-2' }),
                    getMockedAnnotationLabelRef({ id: 'label-3' }),
                ],
            });

            const result = toggleLabel(mockLabel2, annotation.labels);

            expect(result).toEqual([{ id: 'label-1' }, { id: 'label-3' }]);
        });

        it('add label to empty labels array', () => {
            const annotation = getMockedAnnotation({ labels: [] });

            const result = toggleLabel(mockLabel1, annotation.labels);

            expect(result).toEqual([{ id: 'label-1' }]);
        });

        it('remove the only label from annotation', () => {
            const annotation = getMockedAnnotation({
                labels: [getMockedAnnotationLabelRef({ id: 'label-1' })],
            });

            const result = toggleLabel(mockLabel1, annotation.labels);

            expect(result).toEqual([]);
        });
    });
});
