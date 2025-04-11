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

import { useEffect, useRef } from 'react';

import { useMutation, UseMutationResult, useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { ExportDatasetStatusDTO } from '../../../core/configurable-parameters/dtos/configurable-parameters.interface';
import { IntervalJobHandlers } from '../../../core/datasets/hooks/dataset-import.interface';
import { getIntervalJobHandlers } from '../../../core/datasets/hooks/utils';
import { JobExportStatus, JobStatusIdentifier } from '../../../core/jobs/jobs.interface';
import { ExportDatasetIdentifier, ExportDatasetStatusIdentifier } from '../../../core/projects/dataset.interface';
import { isStateDone, isStateError } from '../../../core/projects/hooks/utils';
import QUERY_KEYS from '../../../core/requests/query-keys';
import { useApplicationServices } from '../../../core/services/application-services-provider.component';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { useLocalStorageExportDataset } from './use-local-storage-export-dataset.hook';

export interface UseExportDataset {
    exportDatasetStatus: UseMutationResult<ExportDatasetStatusDTO, AxiosError, ExportDatasetStatusIdentifier>;
    prepareExportDatasetJob: UseMutationResult<{ jobId: string }, AxiosError, ExportDatasetIdentifier>;
    useExportDatasetStatusJob: (params: StatusJobProps<JobExportStatus>) => UseQueryResult<JobExportStatus>;
}

export interface StatusJobProps<T> extends Omit<IntervalJobHandlers<T>, 'onError'> {
    data: JobStatusIdentifier;
    enabled: boolean;
}

export const useExportDataset = (datasetName: string): UseExportDataset => {
    const { projectService } = useApplicationServices();
    const { addNotification, removeNotifications } = useNotification();
    const { addLsExportDataset } = useLocalStorageExportDataset();

    const onError = (error: AxiosError) => {
        addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
    };

    const prepareExportDatasetJob = useMutation({
        mutationFn: projectService.prepareExportDatasetJob,
        onSuccess: ({ jobId }, { datasetId, exportFormat }) => {
            removeNotifications();

            return addLsExportDataset({
                datasetId,
                exportFormat,
                exportDatasetId: jobId,
                isPrepareDone: false,
                datasetName,
            });
        },
        onError,
    });

    const exportDatasetStatus = useMutation({
        mutationFn: projectService.exportDatasetStatus,
        onSuccess: (response, { datasetId }) => {
            if (isStateDone(response.state)) {
                addNotification({
                    message: `Dataset ${datasetId} is ready to download`,
                    type: NOTIFICATION_TYPE.INFO,
                });
            }
            if (isStateError(response.state)) {
                addNotification({ message: response.message, type: NOTIFICATION_TYPE.ERROR });
            }
        },
        onError,
    });

    const useExportDatasetStatusJob = ({
        data,
        enabled = true,
        ...intervalHandlers
    }: StatusJobProps<JobExportStatus>) => {
        const handleSuccessRef = useRef(intervalHandlers);

        const query = useQuery({
            queryKey: QUERY_KEYS.EXPORT_DATASET_STATUS_JOB_KEY(data),
            queryFn: () => projectService.exportDatasetStatusJob(data),
            enabled,
            meta: { notifyOnError: true },
            refetchInterval: 1000,
        });

        useEffect(() => {
            handleSuccessRef.current = intervalHandlers;
        }, [intervalHandlers]);

        useEffect(() => {
            if (!enabled || !query.isSuccess) {
                return;
            }

            getIntervalJobHandlers({ onError, ...handleSuccessRef.current })(query.data);
        }, [enabled, query.isSuccess, query.data]);

        return query;
    };

    return {
        exportDatasetStatus,
        prepareExportDatasetJob,
        useExportDatasetStatusJob,
    };
};
