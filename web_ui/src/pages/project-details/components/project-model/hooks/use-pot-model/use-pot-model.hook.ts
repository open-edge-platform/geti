// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useQueryClient } from '@tanstack/react-query';

import { useModels } from '../../../../../../core/models/hooks/use-models.hook';
import QUERY_KEYS from '../../../../../../core/requests/query-keys';
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
