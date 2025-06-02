// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, ReactNode, useContext } from 'react';

import { paths } from '@geti/core';
import { UseMutationResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isEmpty } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { CreateDatasetBody, CreateDatasetResponse, Dataset } from '../../core/projects/dataset.interface';
import { useProjectDataset } from '../../core/projects/hooks/use-project-dataset.hook';
import { usePinnedCollapsedItems } from '../../hooks/use-pinned-collapsed-items/use-pinned-collapsed-items.hook';
import {
    PinnedCollapsedItemsAction,
    PinnedCollapsedItemsActions,
} from '../../hooks/use-pinned-collapsed-items/use-pinned-collapsed-items.interface';
import { useDatasetIdentifier } from '../../pages/annotator/hooks/use-dataset-identifier.hook';
import { useSelectedDataset } from '../../pages/project-details/components/project-dataset/use-selected-dataset/use-selected-dataset.hook';
import { MAX_NUMBER_OF_DISPLAYED_DATASETS } from '../../pages/project-details/components/project-dataset/utils';
import { useProject } from '../../pages/project-details/providers/project-provider/project-provider.component';
import { MissingProviderError } from '../../shared/missing-provider-error';
import { getUniqueNameFromArray } from '../../shared/utils';
import { useMediaUpload } from '../media-upload-provider/media-upload-provider.component';
import { MediaUploadActionTypes } from '../media-upload-provider/media-upload-reducer-actions';

interface DatasetContextProps {
    selectedDataset: Dataset;
    pinnedDatasets: Dataset[];
    collapsedDatasets: Dataset[];
    handleCreateDataset: () => void;
    handleUpdateDataset: (datasetName: string) => void;
    handleDeleteDataset: () => void;
    handleSelectDataset: (datasetId: string) => void;
    dispatchDatasetsTabs: Dispatch<PinnedCollapsedItemsActions<Dataset>>;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    createDataset: UseMutationResult<CreateDatasetResponse, AxiosError<any, any>, CreateDatasetBody, unknown>;
}
const DatasetContext = createContext<DatasetContextProps | undefined>(undefined);

interface DatasetProviderProps {
    children: ReactNode;
}

export const DatasetProvider = ({ children }: DatasetProviderProps) => {
    const { project, projectIdentifier } = useProject();
    const datasetIdentifier = useDatasetIdentifier();
    const selectedDataset = useSelectedDataset();
    const { dispatch } = useMediaUpload();
    const navigate = useNavigate();

    const { createDataset, updateDataset, deleteDataset } = useProjectDataset();

    const [pinnedDatasets, collapsedDatasets, dispatchDatasetsTabs] = usePinnedCollapsedItems(
        project.datasets,
        selectedDataset.id,
        MAX_NUMBER_OF_DISPLAYED_DATASETS
    );

    const handleCreateDataset = (): void => {
        const datasetName = getUniqueNameFromArray(
            project.datasets.map((dataset) => dataset.name),
            'Testing set '
        );

        createDataset.mutate(
            {
                projectIdentifier,
                name: datasetName,
            },
            {
                onSuccess: (dataset: CreateDatasetResponse) => {
                    dispatchDatasetsTabs({ type: PinnedCollapsedItemsAction.CREATE, payload: dataset });
                    handleSelectDataset(dataset.id);
                },
            }
        );
    };

    const handleUpdateDataset = (datasetName: string): void => {
        const datasetWithTheSameName = project.datasets.filter((dataset) => dataset.name == datasetName);
        const name = !isEmpty(datasetWithTheSameName)
            ? `${datasetName} (${datasetWithTheSameName.length + 1})`
            : datasetName;

        updateDataset.mutate(
            {
                datasetIdentifier,
                updatedDataset: { ...selectedDataset, name },
            },
            {
                onSuccess: () => {
                    dispatchDatasetsTabs({
                        type: PinnedCollapsedItemsAction.UPDATE,
                        payload: { id: datasetIdentifier.datasetId, name },
                    });
                },
            }
        );
    };

    const handleDeleteDataset = (): void => {
        deleteDataset.mutate(datasetIdentifier, {
            onSuccess: () => {
                const trainingDataset =
                    project.datasets.find((dataset) => dataset.useForTraining) || project.datasets[0];

                navigate(paths.project.dataset.index({ ...projectIdentifier, datasetId: trainingDataset.id }));

                dispatchDatasetsTabs({
                    type: PinnedCollapsedItemsAction.REMOVE,
                    payload: { id: datasetIdentifier.datasetId },
                });
                dispatch({ type: MediaUploadActionTypes.REMOVE_UPLOAD_STATE, datasetId: datasetIdentifier.datasetId });
            },
        });
    };

    const handleSelectDataset = (datasetId: string): void => {
        if (datasetId === selectedDataset.id) return;

        dispatchDatasetsTabs({ type: PinnedCollapsedItemsAction.SWAP, payload: { id: datasetId } });
        navigate(paths.project.dataset.media({ ...projectIdentifier, datasetId }));
    };

    return (
        <DatasetContext.Provider
            value={{
                createDataset,
                selectedDataset,
                pinnedDatasets,
                collapsedDatasets,
                handleCreateDataset,
                handleUpdateDataset,
                handleDeleteDataset,
                handleSelectDataset,
                dispatchDatasetsTabs,
            }}
        >
            {children}
        </DatasetContext.Provider>
    );
};

export const useDataset = (): DatasetContextProps => {
    const context = useContext(DatasetContext);

    if (context === undefined) {
        throw new MissingProviderError('useDataset', 'DatasetProvider');
    }

    return context;
};
