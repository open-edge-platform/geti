// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { useAuth } from 'react-oidc-context';
import { v4 as uuid } from 'uuid';

import { useFeatureFlags } from '../../feature-flags/hooks/use-feature-flags.hook';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { ProductInfoEntity, WorkflowId } from '../services/utils.interface';

interface UsePlatformUtils {
    useProductInfo: () => UseQueryResult<ProductInfoEntity, AxiosError>;
    useWorkflowId: () => UseQueryResult<WorkflowId, AxiosError>;
}

const placeholderUuid = uuid();

export const usePlatformUtils = (): UsePlatformUtils => {
    const { FEATURE_FLAG_ANALYTICS_WORKFLOW_ID = false } = useFeatureFlags();
    const auth = useAuth();

    const useProductInfo = (): UseQueryResult<ProductInfoEntity, AxiosError> => {
        const { platformUtilsService } = useApplicationServices();

        return useQuery<ProductInfoEntity, AxiosError>({
            queryKey: QUERY_KEYS.PLATFORM_UTILS_KEYS.VERSION_ENTITY_KEY,
            queryFn: platformUtilsService.getProductInfo,
            meta: { notifyOnError: true },
        });
    };

    const useWorkflowId = (): UseQueryResult<WorkflowId, AxiosError> => {
        return useQuery<WorkflowId, AxiosError>({
            queryKey: QUERY_KEYS.PLATFORM_UTILS_KEYS.WORKFLOW_ID(auth.user?.profile.sub || placeholderUuid),
            queryFn: async () => {
                if (auth && auth.user) {
                    return auth.user.profile.sub;
                }

                return placeholderUuid;
            },
            retry: false,
            enabled: FEATURE_FLAG_ANALYTICS_WORKFLOW_ID,
            placeholderData: placeholderUuid,
        });
    };

    return {
        useProductInfo,
        useWorkflowId,
    };
};
