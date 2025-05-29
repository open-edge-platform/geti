// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryResult, useSuspenseQuery, UseSuspenseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { useAuth } from 'react-oidc-context';
import { v4 as uuid } from 'uuid';

import QUERY_KEYS from '../../../../packages/core/src/requests/query-keys';
import { useFeatureFlags } from '../../feature-flags/hooks/use-feature-flags.hook';
import { ProductInfoEntity, WorkflowId } from '../services/utils.interface';

interface UsePlatformUtils {
    useProductInfo: () => UseSuspenseQueryResult<ProductInfoEntity, AxiosError>;
    useWorkflowId: () => UseQueryResult<WorkflowId, AxiosError>;
}

const placeholderUuid = uuid();

export const usePlatformUtils = (): UsePlatformUtils => {
    const { FEATURE_FLAG_ANALYTICS_WORKFLOW_ID = false } = useFeatureFlags();
    const auth = useAuth();

    const useProductInfo = (): UseSuspenseQueryResult<ProductInfoEntity, AxiosError> => {
        const { platformUtilsService } = useApplicationServices();

        return useSuspenseQuery<ProductInfoEntity, AxiosError>({
            queryKey: QUERY_KEYS.PLATFORM_UTILS_KEYS.VERSION_ENTITY_KEY,
            queryFn: platformUtilsService.getProductInfo,
            meta: { notifyOnError: true },
            staleTime: Infinity,
            gcTime: Infinity,
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
