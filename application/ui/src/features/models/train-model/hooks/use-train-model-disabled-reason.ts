// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useGetDatasetItems } from 'hooks/use-get-dataset-items.hook';
import { useTranslation } from 'react-i18next';

import { i18n } from '../../../../i18n';

const MIN_NUMBER_OF_ANNOTATED_ITEMS = 3;

const SUBSET_TITLE_KEYS = {
    training: 'models.trainingSubsetTitle',
    validation: 'models.validationSubsetTitle',
    testing: 'models.testingSubsetTitle',
} as const;

const getListFormatter = () =>
    new Intl.ListFormat(i18n.language.startsWith('zh') ? 'zh' : 'en', {
        style: 'long',
        type: 'conjunction',
    });

export const useTrainModelDisabledReason = () => {
    const { t } = useTranslation();
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
        return { reason: t('models.trainMinAnnotationsReason') };
    }

    const subsetSizes = [
        { name: 'training', value: trainingSubsetSize },
        { name: 'validation', value: validationSubsetSize },
        { name: 'testing', value: testingSubsetSize },
    ];

    const emptySubsets = subsetSizes.filter(({ value }) => value === 0);

    if (emptySubsets.length === 0 || emptySubsets.length <= reviewedUnassignedSubsetSize) {
        return { reason: undefined };
    }

    const isZh = i18n.language.startsWith('zh');
    const emptySubsetNames = emptySubsets.map(({ name }) =>
        isZh && name in SUBSET_TITLE_KEYS ? t(SUBSET_TITLE_KEYS[name as keyof typeof SUBSET_TITLE_KEYS]) : name
    );
    const emptySubsetText = t('models.emptySubsetText', {
        names: emptySubsetNames.length === 1 ? emptySubsetNames[0] : getListFormatter().format(emptySubsetNames),
        count: emptySubsetNames.length,
    });

    const unannotatedUnassignedSize = unassignedSubsetSize - reviewedUnassignedSubsetSize;

    let assignmentDetail: string;

    if (reviewedUnassignedSubsetSize > 0 && unannotatedUnassignedSize > 0) {
        const reviewedPart = i18n.t('models.assignmentReviewedPart', { count: reviewedUnassignedSubsetSize });
        const unannotatedPart = i18n.t('models.assignmentUnannotatedPart', { count: unannotatedUnassignedSize });
        assignmentDetail = i18n.t('models.assignmentThereAre', {
            detail: reviewedPart,
            unannotatedDetail: unannotatedPart,
        });
    } else if (reviewedUnassignedSubsetSize > 0) {
        assignmentDetail = i18n.t('models.assignmentReviewedOnly', { count: reviewedUnassignedSubsetSize });
    } else if (unannotatedUnassignedSize > 0) {
        assignmentDetail = i18n.t('models.assignmentUnannotatedOnly', { count: unannotatedUnassignedSize });
    } else {
        assignmentDetail = i18n.t('models.assignmentNone');
    }

    return {
        reason: t('models.trainDisabledReason', { emptySubsets: emptySubsetText, assignmentDetail }),
    };
};
