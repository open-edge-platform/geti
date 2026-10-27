// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { useTranslation } from '@/i18n';
import { Flex } from '@geti-ui/ui';
import { partition } from 'lodash-es';

import { SortModelArchitectures } from '../sort-model-architectures/sort-model-architectures.component';
import { getSortOptions, SORTING_HANDLERS, SortingOptions } from '../sort-model-architectures/utils';
import { TIMM_MODEL_ARCHITECTURE_ID } from '../timm-model-configuration/utils';
import { useTrainModelState } from '../train-model-provider.component';
import { ModelArchitecture } from './model-architecture.component';
import { ModelArchitecturesListLayout } from './model-architectures-list-layout/model-architectures-list-layout.component';

export const ModelArchitecturesList = () => {
    const { t } = useTranslation();
    const { modelArchitectures, selectedModelArchitectureId, onSelectModelArchitectureId } = useTrainModelState();
    const [sortBy, setSortBy] = useState<SortingOptions>(SortingOptions.RECOMMENDED);
    const [[timmCard], sortableModelArchitectures] = partition(
        modelArchitectures,
        (modelArchitecture) => modelArchitecture.id === TIMM_MODEL_ARCHITECTURE_ID
    );
    const sortedModelArchitectures = SORTING_HANDLERS[sortBy](sortableModelArchitectures);
    // The TIMM card always stays last, regardless of the active sort.
    const modelArchitecturesToRender =
        timmCard === undefined ? sortedModelArchitectures : [...sortedModelArchitectures, timmCard];

    return (
        <Flex direction={'column'} gap={'size-200'}>
            <SortModelArchitectures sortBy={sortBy} onSort={setSortBy} items={getSortOptions(t)} />
            <ModelArchitecturesListLayout
                selectedModelArchitectureId={selectedModelArchitectureId}
                onSelectedModelArchitectureIdChange={onSelectModelArchitectureId}
                ariaLabel={'Model architectures'}
            >
                {modelArchitecturesToRender.map((modelArchitecture) => (
                    <ModelArchitecture
                        key={modelArchitecture.id}
                        modelArchitecture={modelArchitecture}
                        selectedModelArchitectureId={selectedModelArchitectureId}
                        onSelectedModelArchitectureIdChange={onSelectModelArchitectureId}
                    />
                ))}
            </ModelArchitecturesListLayout>
        </Flex>
    );
};
