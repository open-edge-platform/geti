// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { useGetDatasetItems } from 'hooks/use-get-dataset-items.hook';

const MIN_NUMBER_OF_ANNOTATED_ITEMS = 3;

export const useTrainModelDisabledReason = () => {
    const { t, i18n } = useTranslation();
    const listFormatter = new Intl.ListFormat(i18n.resolvedLanguage ?? i18n.language, {
        style: 'long',
        type: 'conjunction',
    });

    const { totalCount, isPending: isTotalPending } = useGetDatasetItems({ annotationStatus: 'with_annotations' });
    const { totalCount: trainingSubsetSize, isPending: isTrainingPending } = useGetDatasetItems({
        annotationStatus: 'with_annotations',
        subsets: ['training'],
    });
    const { totalCount: testingSubsetSize, isPending: isTestingPending } = useGetDatasetItems({
        annotationStatus: 'with_annotations',
        subsets: ['testing'],
    });
    const { totalCount: validationSubsetSize, isPending: isValidationPending } = useGetDatasetItems({
        annotationStatus: 'with_annotations',
        subsets: ['validation'],
    });
    const { totalCount: reviewedUnassignedSubsetSize, isPending: isReviewedUnassignedPending } = useGetDatasetItems({
        annotationStatus: 'with_annotations',
        subsets: ['unassigned'],
    });
    const { totalCount: unassignedSubsetSize, isPending: isUnassignedPending } = useGetDatasetItems({
        subsets: ['unassigned'],
    });

    if (
        isTotalPending ||
        isTrainingPending ||
        isTestingPending ||
        isValidationPending ||
        isReviewedUnassignedPending ||
        isUnassignedPending
    ) {
        return { reason: undefined };
    }

    if (totalCount < MIN_NUMBER_OF_ANNOTATED_ITEMS) {
        return {
            reason: t('models.training.validation.notEnoughAnnotations'),
        };
    }

    const subsetSizes = [
        { label: t('common.labels.trainingLowercase'), value: trainingSubsetSize },
        { label: t('common.labels.validationLowercase'), value: validationSubsetSize },
        { label: t('common.labels.testingLowercase'), value: testingSubsetSize },
    ];

    const emptySubsets = subsetSizes.filter(({ value }) => value === 0);

    if (emptySubsets.length === 0 || emptySubsets.length <= reviewedUnassignedSubsetSize) {
        return { reason: undefined };
    }

    const emptySubsetNames = emptySubsets.map(({ label }) => label);
    const subsetClause = t('models.training.validation.emptySubsetClause', {
        count: emptySubsetNames.length,
        list: listFormatter.format(emptySubsetNames),
    });

    const unannotatedUnassignedSize = unassignedSubsetSize - reviewedUnassignedSubsetSize;

    let assignmentDetail: string;

    if (reviewedUnassignedSubsetSize > 0 && unannotatedUnassignedSize > 0) {
        assignmentDetail = t('models.training.validation.mixedAssignmentDetail', {
            reviewedClause: t('models.training.validation.mixedReviewedClause', {
                count: reviewedUnassignedSubsetSize,
            }),
            unannotatedClause: t('models.training.validation.mixedUnannotatedClause', {
                count: unannotatedUnassignedSize,
            }),
        });
    } else if (reviewedUnassignedSubsetSize > 0) {
        assignmentDetail = t('models.training.validation.reviewedOnly', { count: reviewedUnassignedSubsetSize });
    } else if (unannotatedUnassignedSize > 0) {
        assignmentDetail = t('models.training.validation.unannotatedOnly', { count: unannotatedUnassignedSize });
    } else {
        assignmentDetail = t('models.training.validation.noUnassignedItems');
    }

    return {
        reason: t('models.training.validation.emptySubsetsReason', { subsetClause, assignmentDetail }),
    };
};
