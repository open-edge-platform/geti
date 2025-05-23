// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { DOMAIN, ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { SupportedAlgorithm } from '../supported-algorithms.interface';

export const useSupportedAlgorithms = (
    projectIdentifier: ProjectIdentifier,
    domain?: DOMAIN
): UseQueryResult<SupportedAlgorithm[], AxiosError> => {
    const { supportedAlgorithmsService } = useApplicationServices();

    return useQuery<SupportedAlgorithm[], AxiosError>({
        queryKey: QUERY_KEYS.SUPPORTED_ALGORITHMS(domain),
        queryFn: () => {
            return supportedAlgorithmsService.getProjectSupportedAlgorithms(projectIdentifier);
        },
        meta: { notifyOnError: true },
    });
};
