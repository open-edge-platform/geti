// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';
import localforage from 'localforage';

import { createInMemoryProjectService } from '../../core/projects/services/in-memory-project-service';
import { GETI_CAMERA_INDEXEDDB_INSTANCE_NAME } from '../../pages/camera-support/camera.interface';
import { getMockedProject } from '../../test-utils/mocked-items-factory/mocked-project';
import { projectRender } from '../../test-utils/project-provider-render';
import { clearAllStorage, clearDatasetStorage, useClearProjectStorage } from './use-clear-indexeddb-storage.hook';

describe('Clear indexeddb storage', () => {
    let spy: jest.SpyInstance;

    beforeEach(() => {
        jest.clearAllMocks();
        spy = jest.spyOn(localforage, 'dropInstance');
    });

    it('clearAllStorage clears all storage correctly', () => {
        clearAllStorage();

        expect(spy).toHaveBeenCalledWith({ name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME });
    });

    it('clearDatasetStorage clears dataset storage correctly', () => {
        clearDatasetStorage('12345');

        expect(spy).toHaveBeenCalledWith({ storeName: 'dataset-12345', name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME });
    });

    it('clearDatasetStorage clears project storage correctly', async () => {
        const projectService = createInMemoryProjectService();

        const mockProject = getMockedProject({
            id: '123',
            datasets: [
                {
                    id: 'id-1',
                    name: 'Dataset 1',
                    creationTime: '2022-07-22T20:09:22.577000+00:00',
                    useForTraining: true,
                },
                {
                    id: 'id-2',
                    name: 'Dataset 2',
                    creationTime: '2022-07-22T20:09:22.578000+00:00',
                    useForTraining: false,
                },
                {
                    id: 'id-3',
                    name: 'Dataset 3',
                    creationTime: '2022-07-22T20:09:22.579000+00:00',
                    useForTraining: false,
                },
            ],
        });

        projectService.getProject = async () => mockProject;

        const App = () => {
            const { clearProjectStorage } = useClearProjectStorage({
                workspaceId: 'workspace-id',
                organizationId: 'organizationId',
                projectId: '123',
            });

            clearProjectStorage?.();

            return <></>;
        };

        await projectRender(<App />, { services: { projectService } });

        await waitFor(() => {
            expect(spy).toHaveBeenNthCalledWith(1, {
                storeName: 'dataset-id-1',
                name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME,
            });
            expect(spy).toHaveBeenNthCalledWith(2, {
                storeName: 'dataset-id-2',
                name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME,
            });
            expect(spy).toHaveBeenNthCalledWith(3, {
                storeName: 'dataset-id-3',
                name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME,
            });
        });
    });
});
