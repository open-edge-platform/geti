// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useFeatureFlags } from '../../feature-flags/hooks/use-feature-flags.hook';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { useDeploymentConfigQuery } from '../../services/use-deployment-config-query.hook';
import { MaintenanceResponse } from '../services/maintenance.interface';

export const useMaintenanceQuery = (): UseQueryResult<MaintenanceResponse, AxiosError> => {
    const { maintenanceService } = useApplicationServices();
    const { data } = useDeploymentConfigQuery();
    const { FEATURE_FLAG_MAINTENANCE_BANNER } = useFeatureFlags();
    const isSaasEnv = useIsSaasEnv();

    return useQuery<MaintenanceResponse, AxiosError>({
        queryKey: QUERY_KEYS.MAINTENANCE,
        queryFn: () => maintenanceService.getMaintenanceInfo(data?.configUrl ?? ''),
        enabled: Boolean(FEATURE_FLAG_MAINTENANCE_BANNER && isSaasEnv && data?.configUrl),
        retry: 0,
        throwOnError: false,
    });
};
