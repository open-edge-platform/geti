// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation, UseMutationResult, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { clearDatasetStorage } from '../../../hooks/use-clear-indexeddb-storage/use-clear-indexeddb-storage.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import QUERY_KEYS from '../../requests/query-keys';
import {
    CreateDatasetBody,
    CreateDatasetResponse,
    Dataset,
    DatasetIdentifier,
    DeleteDatasetResponse,
} from '../dataset.interface';

interface UpdateDatasetBody {
    datasetIdentifier: DatasetIdentifier;
    updatedDataset: Dataset;
}

interface UseProjectDataset {
    createDataset: UseMutationResult<CreateDatasetResponse, AxiosError, CreateDatasetBody>;
    updateDataset: UseMutationResult<CreateDatasetResponse, AxiosError, UpdateDatasetBody>;
    deleteDataset: UseMutationResult<DeleteDatasetResponse, AxiosError, DatasetIdentifier>;
}

export const useProjectDataset = (): UseProjectDataset => {
    const service = useApplicationServices().projectService;
    const client = useQueryClient();

    const { addNotification } = useNotification();

    const createDataset = useMutation<CreateDatasetResponse, AxiosError, CreateDatasetBody>({
        mutationFn: service.createDataset,
        onSuccess: async (_, variables) => {
            await client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_KEY(variables.projectIdentifier) });
        },
        onError: (error: AxiosError) => {
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    const deleteDataset = useMutation<DeleteDatasetResponse, AxiosError, DatasetIdentifier>({
        mutationFn: service.deleteDataset,
        onSuccess: async (_, variables) => {
            clearDatasetStorage(variables.datasetId);

            await client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_KEY(variables) });
        },
        onError: (error: AxiosError) => {
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    const updateDataset = useMutation({
        mutationFn: ({ datasetIdentifier, updatedDataset }: UpdateDatasetBody) => {
            return service.updateDataset(datasetIdentifier, updatedDataset);
        },

        onSuccess: async (_, variables) => {
            await client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_KEY(variables.datasetIdentifier) });
        },

        onError: (error: AxiosError) => {
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    return { createDataset, updateDataset, deleteDataset };
};
