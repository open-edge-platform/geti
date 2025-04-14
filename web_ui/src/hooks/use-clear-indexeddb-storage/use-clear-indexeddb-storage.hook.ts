// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import localforage from 'localforage';

import { ProjectIdentifier } from '../../core/projects/core.interface';
import { useProjectActions } from '../../core/projects/hooks/use-project-actions.hook';
import { GETI_CAMERA_INDEXEDDB_INSTANCE_NAME } from '../../pages/camera-support/camera.interface';

export const useClearProjectStorage = (projectIdentifier: ProjectIdentifier) => {
    const { useGetProject } = useProjectActions();

    const { data: project } = useGetProject(projectIdentifier);

    const clearProjectStorage = () => {
        project?.datasets.forEach((dataset) => {
            clearDatasetStorage(dataset.id);
        });
    };

    return { clearProjectStorage: project === undefined ? undefined : clearProjectStorage };
};

export const clearDatasetStorage = (datasetId: string) => {
    return localforage.dropInstance({ storeName: `dataset-${datasetId}`, name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME });
};

export const clearAllStorage = () => {
    return localforage.dropInstance({ name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME });
};
