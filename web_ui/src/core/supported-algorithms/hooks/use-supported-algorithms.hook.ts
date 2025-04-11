// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
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

import { DOMAIN, ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
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
