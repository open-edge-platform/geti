// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Divider } from '@adobe/react-spectrum';
import { isEmpty, partition } from 'lodash-es';

import { PerformanceCategory } from '../../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { ModelArchitecturesList } from './model-architectures-list.component';
import { moveActiveArchitectureToBeRightAfterRecommended, SortingOptions } from './utils';

interface ModelArchitecturesMainContentProps {
    algorithms: SupportedAlgorithm[];
    selectedModelTemplateId: string | null;
    onChangeSelectedTemplateId: (modelTemplateId: string | null) => void;
    activeModelTemplateId: string | null;
    sortBy: SortingOptions;
}

export const ModelArchitecturesMainContent: FC<ModelArchitecturesMainContentProps> = ({
    algorithms,
    selectedModelTemplateId,
    onChangeSelectedTemplateId,
    activeModelTemplateId,
    sortBy,
}) => {
    const [otherAlgorithms, recommendedAlgorithms] = partition(
        algorithms,
        (algorithm) => algorithm.performanceCategory === PerformanceCategory.OTHER
    );

    if (sortBy !== SortingOptions.RELEVANCE) {
        return (
            <ModelArchitecturesList
                algorithms={algorithms}
                selectedModelTemplateId={selectedModelTemplateId}
                onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                activeModelTemplateId={activeModelTemplateId}
            />
        );
    }

    const [sortedOtherAlgorithms, sortedRecommendedAlgorithms] = moveActiveArchitectureToBeRightAfterRecommended(
        recommendedAlgorithms,
        otherAlgorithms,
        activeModelTemplateId
    );

    if (isEmpty(otherAlgorithms)) {
        return (
            <ModelArchitecturesList
                algorithms={sortedRecommendedAlgorithms}
                selectedModelTemplateId={selectedModelTemplateId}
                onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                activeModelTemplateId={activeModelTemplateId}
            />
        );
    }

    return (
        <>
            <ModelArchitecturesList
                algorithms={sortedRecommendedAlgorithms}
                selectedModelTemplateId={selectedModelTemplateId}
                onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                activeModelTemplateId={activeModelTemplateId}
            />
            <Divider size={'S'} marginY={'size-250'} />
            <ModelArchitecturesList
                algorithms={sortedOtherAlgorithms}
                selectedModelTemplateId={selectedModelTemplateId}
                onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                activeModelTemplateId={activeModelTemplateId}
            />
        </>
    );
};
