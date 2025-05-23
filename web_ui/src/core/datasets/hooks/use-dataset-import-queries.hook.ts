// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation, UseMutationResult, useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import {
    JobImportDatasetToExistingProjectStatus,
    JobImportDatasetToNewProjectStatus,
    JobPrepareDatasetImportNewProjectStatus,
    JobPrepareDatasetToExistingProjectStatus,
    JobStatusIdentifier,
} from '../../jobs/jobs.interface';
import { CreateDatasetResponse } from '../../projects/dataset.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { getErrorMessage } from '../../services/utils';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import {
    DatasetImportIdentifier,
    DatasetImportPrepareForNewProjectResponse,
    DatasetImportToExistingProjectIdentifier,
    DatasetImportToNewProjectIdentifier,
    DatasetImportToNewProjectResponse,
    DatasetPrepareForExistingProjectIdentifier,
    DatasetPrepareForExistingProjectResponse,
} from '../dataset.interface';
import { IntervalJobHandlers } from './dataset-import.interface';
import { getIntervalJobHandlers } from './utils';

interface StatusJobProps<T> extends IntervalJobHandlers<T> {
    data: JobStatusIdentifier;
    enabled: boolean;
}

interface UseDatasetImportQueries {
    prepareDatasetForNewProject: UseMutationResult<
        DatasetImportPrepareForNewProjectResponse,
        AxiosError,
        DatasetImportIdentifier
    >;
    prepareDatasetJob: UseMutationResult<{ jobId: string }, AxiosError, DatasetImportIdentifier>;
    importDatasetToNewProject: UseMutationResult<
        DatasetImportToNewProjectResponse,
        AxiosError,
        DatasetImportToNewProjectIdentifier
    >;

    prepareDatasetToExistingProject: UseMutationResult<
        DatasetPrepareForExistingProjectResponse,
        AxiosError,
        DatasetPrepareForExistingProjectIdentifier
    >;
    prepareDatasetToExistingProjectJob: UseMutationResult<
        { jobId: string },
        AxiosError,
        DatasetPrepareForExistingProjectIdentifier
    >;

    importDatasetToNewProjectJob: UseMutationResult<{ jobId: string }, AxiosError, DatasetImportToNewProjectIdentifier>;

    importDatasetToExistingProject: UseMutationResult<
        CreateDatasetResponse,
        AxiosError,
        DatasetImportToExistingProjectIdentifier
    >;
    importDatasetToExistingProjectJob: UseMutationResult<
        { jobId: string },
        AxiosError,
        DatasetImportToExistingProjectIdentifier
    >;

    deleteImportProjectFromDataset: UseMutationResult<void, AxiosError, WorkspaceIdentifier & { fileId: string }>;

    usePreparingStatusJob: (
        config: StatusJobProps<JobPrepareDatasetImportNewProjectStatus>
    ) => UseQueryResult<JobPrepareDatasetImportNewProjectStatus, AxiosError>;

    useImportingStatusJob: (
        config: StatusJobProps<JobImportDatasetToNewProjectStatus>
    ) => UseQueryResult<JobImportDatasetToNewProjectStatus, AxiosError>;

    usePreparingExistingProjectStatusJob: (
        config: StatusJobProps<JobPrepareDatasetToExistingProjectStatus>
    ) => UseQueryResult<JobPrepareDatasetToExistingProjectStatus, AxiosError>;

    useImportingExistingProjectStatusJob: ({
        data,
        enabled,
        onSuccess,
        onError,
    }: StatusJobProps<JobImportDatasetToExistingProjectStatus>) => UseQueryResult<
        JobImportDatasetToExistingProjectStatus,
        AxiosError
    >;
}

export const useDatasetImportQueries = (): UseDatasetImportQueries => {
    const { addNotification } = useNotification();
    const { datasetImportService: service } = useApplicationServices();

    const prepareDatasetForNewProject: UseDatasetImportQueries['prepareDatasetForNewProject'] = useMutation({
        mutationFn: service.prepareDatasetForNewProject,
    });

    const prepareDatasetJob: UseDatasetImportQueries['prepareDatasetJob'] = useMutation({
        mutationFn: service.prepareDatasetJob,
    });

    const importDatasetToNewProject: UseDatasetImportQueries['importDatasetToNewProject'] = useMutation({
        mutationFn: service.importDatasetToNewProject,
        onError: (error: AxiosError) => {
            addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
        },
    });

    const importDatasetToNewProjectJob: UseDatasetImportQueries['importDatasetToNewProjectJob'] = useMutation({
        mutationFn: service.importDatasetToNewProjectJob,
    });

    const prepareDatasetToExistingProject: UseDatasetImportQueries['prepareDatasetToExistingProject'] = useMutation({
        mutationFn: service.prepareDatasetToExistingProject,
    });

    const prepareDatasetToExistingProjectJob: UseDatasetImportQueries['prepareDatasetToExistingProjectJob'] =
        useMutation({ mutationFn: service.prepareDatasetToExistingProjectJob });

    const importDatasetToExistingProject: UseDatasetImportQueries['importDatasetToExistingProject'] = useMutation({
        mutationFn: service.importDatasetToExistingProject,
    });

    const importDatasetToExistingProjectJob: UseDatasetImportQueries['importDatasetToExistingProjectJob'] = useMutation(
        { mutationFn: service.importDatasetToExistingProjectJob }
    );

    const usePreparingStatusJob: UseDatasetImportQueries['usePreparingStatusJob'] = ({
        data,
        enabled = true,
        ...intervalHandlers
    }) => {
        const intervalHandlersRef = useRef(intervalHandlers);

        const query = useQuery<JobPrepareDatasetImportNewProjectStatus, AxiosError>({
            queryKey: QUERY_KEYS.PREPARE_DATASET_STATUS_JOB_KEY(data),
            queryFn: () => service.prepareDatasetImportNewProjectJob(data),
            enabled,
            refetchInterval: 1000,
        });

        useEffect(() => {
            intervalHandlersRef.current = intervalHandlers;
        }, [intervalHandlers]);

        useEffect(() => {
            if (!enabled || !query.isSuccess) {
                return;
            }
            getIntervalJobHandlers(intervalHandlersRef.current)(query.data);
        }, [enabled, query.isSuccess, query.data]);

        useEffect(() => {
            if (!query.isError || query.error === null) {
                return;
            }

            intervalHandlersRef.current.onError(query.error);
        }, [query.isError, query.error]);

        return query;
    };

    const useImportingStatusJob: UseDatasetImportQueries['useImportingStatusJob'] = ({
        data,
        enabled = true,
        ...intervalHandlers
    }) => {
        const intervalHandlersRef = useRef(intervalHandlers);

        const query = useQuery<JobImportDatasetToNewProjectStatus, AxiosError>({
            queryKey: QUERY_KEYS.IMPORT_DATASET_NEW_PROJECT_STATUS_JOB_KEY(data),
            queryFn: () => service.importDatasetToNewProjectStatusJob(data),
            enabled,
            refetchInterval: 1000,
        });

        useEffect(() => {
            intervalHandlersRef.current = intervalHandlers;
        }, [intervalHandlers]);

        useEffect(() => {
            if (!enabled || !query.isSuccess) {
                return;
            }
            getIntervalJobHandlers(intervalHandlersRef.current)(query.data);
        }, [enabled, query.isSuccess, query.data]);

        useEffect(() => {
            if (!query.isError || query.error === null) {
                return;
            }

            intervalHandlersRef.current.onError(query.error);
        }, [query.isError, query.error]);

        return query;
    };

    const usePreparingExistingProjectStatusJob: UseDatasetImportQueries['usePreparingExistingProjectStatusJob'] = ({
        data,
        enabled = true,
        ...intervalHandlers
    }) => {
        const intervalHandlersRef = useRef(intervalHandlers);

        const query = useQuery<JobPrepareDatasetToExistingProjectStatus, AxiosError>({
            queryKey: QUERY_KEYS.PREPARE_DATASET_STATUS_JOB_KEY(data),
            queryFn: () => service.prepareDatasetToExistingProjectStatusJob(data),
            enabled,
            refetchInterval: 1000,
        });

        useEffect(() => {
            intervalHandlersRef.current = intervalHandlers;
        }, [intervalHandlers]);

        useEffect(() => {
            if (!enabled || !query.isSuccess) {
                return;
            }
            getIntervalJobHandlers(intervalHandlersRef.current)(query.data);
        }, [enabled, query.isSuccess, query.data]);

        useEffect(() => {
            if (!query.isError || query.error === null) {
                return;
            }

            intervalHandlersRef.current.onError(query.error);
        }, [query.isError, query.error]);

        return query;
    };

    const useImportingExistingProjectStatusJob: UseDatasetImportQueries['useImportingExistingProjectStatusJob'] = ({
        data,
        enabled = true,
        ...intervalHandlers
    }) => {
        const intervalHandlersRef = useRef(intervalHandlers);

        const query = useQuery<JobImportDatasetToExistingProjectStatus, AxiosError>({
            queryKey: QUERY_KEYS.IMPORT_DATASET_EXISTING_PROJECT_STATUS_JOB_KEY(data),
            queryFn: () => service.importDatasetToExistingProjectStatusJob(data),
            enabled,
            refetchInterval: 1000,
        });

        useEffect(() => {
            intervalHandlersRef.current = intervalHandlers;
        }, [intervalHandlers]);

        useEffect(() => {
            if (!enabled || !query.isSuccess) {
                return;
            }

            getIntervalJobHandlers(intervalHandlersRef.current)(query.data);
        }, [enabled, query.isSuccess, query.data]);

        useEffect(() => {
            if (!query.isError || query.error === null) {
                return;
            }

            intervalHandlersRef.current.onError(query.error);
        }, [query.isError, query.error]);

        return query;
    };

    const deleteImportProjectFromDataset: UseDatasetImportQueries['deleteImportProjectFromDataset'] = useMutation({
        mutationFn: service.deleteImportProjectFromDataset,
    });

    return {
        prepareDatasetForNewProject,
        prepareDatasetJob,
        importDatasetToNewProject,
        importDatasetToNewProjectJob,
        usePreparingStatusJob,
        useImportingStatusJob,

        prepareDatasetToExistingProject,
        prepareDatasetToExistingProjectJob,

        importDatasetToExistingProject,
        importDatasetToExistingProjectJob,
        usePreparingExistingProjectStatusJob,
        useImportingExistingProjectStatusJob,

        deleteImportProjectFromDataset,
    };
};
