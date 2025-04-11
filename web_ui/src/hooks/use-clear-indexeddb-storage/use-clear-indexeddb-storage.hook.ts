// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
