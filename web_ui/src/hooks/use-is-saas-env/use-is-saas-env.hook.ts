// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useDeploymentConfigQuery } from '@geti/core/src/services/use-deployment-config-query.hook';

export const useIsSaasEnv = (): boolean => {
    const deploymentConfig = useDeploymentConfigQuery();

    return deploymentConfig?.data?.servingMode === 'saas';
};
