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

import { useEffect } from 'react';

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { ModelIdentifier } from '../../models/models.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { ModelMetrics } from '../model-statistics.interface';

export const useModelStatistics = (modelIdentifier: ModelIdentifier): UseQueryResult<ModelMetrics, AxiosError> => {
    const service = useApplicationServices().modelStatisticsService;
    const { addNotification } = useNotification();

    const modelStatisticsQuery = useQuery<ModelMetrics, AxiosError>({
        queryKey: QUERY_KEYS.MODEL_STATISTICS_KEY(modelIdentifier),
        queryFn: () => {
            return service.getModelStatistics(modelIdentifier);
        },
        retry: 1,
    });

    useEffect(() => {
        if (!modelStatisticsQuery.isError || modelStatisticsQuery.error === undefined) {
            return;
        }

        if (modelStatisticsQuery.error.response?.status === StatusCodes.NOT_FOUND) {
            addNotification({ message: getErrorMessage(modelStatisticsQuery.error), type: NOTIFICATION_TYPE.ERROR });
        }
    }, [modelStatisticsQuery.isError, modelStatisticsQuery.error, addNotification]);

    return modelStatisticsQuery;
};
