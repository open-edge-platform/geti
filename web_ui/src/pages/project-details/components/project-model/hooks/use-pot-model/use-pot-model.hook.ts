// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useQueryClient } from '@tanstack/react-query';

import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import { useModelIdentifier } from '../../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { NOTIFICATION_TYPE } from '../../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../../notification/notification.component';
import { STARTED_OPTIMIZATION } from '../../model-variants/utils';

interface UsePOTModel {
    optimizePOTModel: () => void;
    isLoading: boolean;
}

export const usePOTModel = (): UsePOTModel => {
    const modelIdentifier = useModelIdentifier();
    const { useOptimizeModelMutation } = useModels();
    const optimizeModel = useOptimizeModelMutation();
    const { addNotification } = useNotification();
    const queryClient = useQueryClient();

    const optimizePOTModel = (): void => {
        optimizeModel.mutate(
            { modelIdentifier },
            {
                onSuccess: async () => {
                    addNotification({ message: STARTED_OPTIMIZATION, type: NOTIFICATION_TYPE.INFO });

                    await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.MODEL_KEY(modelIdentifier) });
                },
            }
        );
    };

    return {
        optimizePOTModel,
        isLoading: optimizeModel.isPending,
    };
};
