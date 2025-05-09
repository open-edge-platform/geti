// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { isEmpty } from 'lodash-es';

import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { useModelIdentifier } from '../../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { UseOptimizedModels } from './use-optimized-models.hook.interface';

export const useOptimizedModels = (): UseOptimizedModels => {
    const modelIdentifier = useModelIdentifier();
    const { useModelQuery } = useModels();
    const { data, refetch: refetchModels } = useModelQuery(modelIdentifier);

    const isPOTModel = useMemo(
        () => !!data?.optimizedModels.find(({ optimizationType }) => optimizationType === 'POT'),
        [data?.optimizedModels]
    );

    const areOptimizedModelsVisible = !isEmpty(data?.optimizedModels);

    return {
        modelDetails: data,
        isPOTModel,
        areOptimizedModelsVisible,
        refetchModels,
    };
};
