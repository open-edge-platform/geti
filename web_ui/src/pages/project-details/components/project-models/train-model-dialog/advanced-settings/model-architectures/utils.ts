// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import partition from 'lodash/partition';

import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';

export enum SortingOptions {
    RELEVANCE = 'relevance',
    SIZE_DESC = 'size-desc',
    SIZE_ASC = 'size-asc',
    COMPLEXITY_DESC = 'complexity-desc',
    COMPLEXITY_ASC = 'complexity-asc',
}

export const moveActiveArchitectureToBeRightAfterRecommended = (
    recommendedAlgorithms: SupportedAlgorithm[],
    otherAlgorithms: SupportedAlgorithm[],
    activeModelTemplateId: string | null
): [SupportedAlgorithm[], SupportedAlgorithm[]] => {
    if (activeModelTemplateId === null) {
        return [otherAlgorithms, recommendedAlgorithms];
    }

    if (recommendedAlgorithms.some((algorithm) => algorithm.modelTemplateId === activeModelTemplateId)) {
        return [otherAlgorithms, recommendedAlgorithms];
    }

    const [activeAlgorithm, rest] = partition(
        otherAlgorithms,
        (algorithm) => algorithm.modelTemplateId === activeModelTemplateId
    );

    return [activeAlgorithm.concat(...rest), recommendedAlgorithms];
};
