// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationDTO } from '@/api/types';
import { v4 as uuid } from 'uuid';

import type { Annotation, AnnotationLabelRef } from '../types';

export const mapServerAnnotationsToLocal = (serverAnnotations: AnnotationDTO[]): Annotation[] => {
    return serverAnnotations.map((annotation) => {
        const labels: AnnotationLabelRef[] = (annotation.labels ?? []).map((labelRef, idx) => {
            const probability = annotation.confidences?.at(idx);

            if (probability !== undefined) {
                return { id: labelRef.id, probability };
            }

            return { id: labelRef.id };
        });

        return {
            shape: annotation.shape,
            id: uuid(),
            labels,
        };
    });
};

export const mapLocalAnnotationsToServer = (
    localAnnotations: Annotation[],
    validLabelIds?: Set<string>
): AnnotationDTO[] => {
    return localAnnotations.map((annotation) => {
        const filteredLabels = validLabelIds
            ? annotation.labels.filter((ref) => validLabelIds.has(ref.id))
            : annotation.labels;

        const hasProbabilities = filteredLabels.some((ref) => ref.probability !== undefined);

        const confidences = hasProbabilities
            ? filteredLabels
                  .filter((labelRef): labelRef is Required<AnnotationLabelRef> => labelRef.probability !== undefined)
                  .map((labelRef) => labelRef.probability)
            : null;

        return {
            labels: filteredLabels.map(({ id }) => ({ id })),
            shape: annotation.shape,
            confidences,
        };
    });
};
