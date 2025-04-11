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

import { ReactNode } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';

import { clearDatasetStorage } from '../../../hooks/use-clear-indexeddb-storage/use-clear-indexeddb-storage.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { getMockedDataset } from '../../../test-utils/mocked-items-factory/mocked-datasets';
import { ApplicationServicesProvider } from '../../services/application-services-provider.component';
import { CreateDatasetBody, CreateDatasetResponse, DeleteDatasetResponse } from '../dataset.interface';
import { createInMemoryProjectService } from '../services/in-memory-project-service';
import { ProjectService } from '../services/project-service.interface';
import { useProjectDataset } from './use-project-dataset.hook';

const mockClearDatasetStorage = jest.fn();
jest.mock('../../../hooks/use-clear-indexeddb-storage/use-clear-indexeddb-storage.hook', () => ({
    ...jest.requireActual('../../../hooks/use-clear-indexeddb-storage/use-clear-indexeddb-storage.hook'),
    clearDatasetStorage: jest.fn(() => mockClearDatasetStorage),
}));

const mockAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

const wrapper = ({
    children,
    projectService,
    queryClient,
}: {
    children?: ReactNode;
    projectService: ProjectService;
    queryClient: QueryClient;
}) => {
    return (
        <ApplicationServicesProvider useInMemoryEnvironment projectService={projectService}>
            <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        </ApplicationServicesProvider>
    );
};

const mockDatasetIdentifier = {
    organizationId: 'organization-id',
    workspaceId: 'workspace_1',
    projectId: 'project-id',
    datasetId: 'dataset_1',
};
const mockCreateDatasetBody: CreateDatasetBody = {
    projectIdentifier: {
        organizationId: 'organization-id',
        workspaceId: '1',
        projectId: '4',
    },
    name: 'some-dataset',
};
const projectService = createInMemoryProjectService();

const renderProjectDatasetHook = (params: { projectService: ProjectService; queryClient: QueryClient }) => {
    return renderHook(() => useProjectDataset(), {
        wrapper: ({ children }) =>
            wrapper({ children, projectService: params.projectService, queryClient: params.queryClient }),
    });
};

describe('useProjectDataset', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('useCreateDataset', () => {
        const queryClient = new QueryClient();
        const mockInvalidateQueries = jest.fn();

        queryClient.invalidateQueries = mockInvalidateQueries;

        it('mockInvalidateQueries is called when the call succeeds', async () => {
            projectService.createDataset = jest.fn(
                (): Promise<CreateDatasetResponse> => Promise.resolve(getMockedDataset())
            );

            const { result } = renderProjectDatasetHook({ projectService, queryClient });

            act(() => {
                result.current.createDataset.mutate(mockCreateDatasetBody);
            });

            await waitFor(() => {
                expect(mockInvalidateQueries).toHaveBeenCalled();
            });

            expect(mockAddNotification).not.toHaveBeenCalled();
            expect(projectService.createDataset).toHaveBeenCalledWith(mockCreateDatasetBody);
        });

        it('addNotification is called when the call fails', async () => {
            const error = { message: 'test' };

            projectService.createDataset = jest.fn((): Promise<CreateDatasetResponse> => Promise.reject(error));

            const { result } = renderProjectDatasetHook({ projectService, queryClient });

            act(() => {
                result.current.createDataset.mutate(mockCreateDatasetBody);
            });

            await waitFor(() => {
                expect(projectService.createDataset).toHaveBeenCalledWith(mockCreateDatasetBody);
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: error.message,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });
    });

    describe('useDeleteDataset', () => {
        const queryClient = new QueryClient();
        const mockInvalidateQueries = jest.fn();

        queryClient.invalidateQueries = mockInvalidateQueries;

        it('mockInvalidateQueries is called when the call succeeds', async () => {
            projectService.deleteDataset = jest.fn(
                (): Promise<DeleteDatasetResponse> => Promise.resolve({ result: 'ok' })
            );

            const { result } = renderProjectDatasetHook({ projectService, queryClient });

            act(() => {
                result.current.deleteDataset.mutate(mockDatasetIdentifier);
            });

            await waitFor(() => {
                expect(mockInvalidateQueries).toHaveBeenCalled();
                expect(mockAddNotification).not.toHaveBeenCalled();
                expect(clearDatasetStorage).toHaveBeenCalledWith('dataset_1');
                expect(projectService.deleteDataset).toHaveBeenCalledWith(mockDatasetIdentifier);
            });
        });

        it('addNotification is called when the call fails', async () => {
            const error = { message: 'test' };

            projectService.deleteDataset = jest.fn((): Promise<DeleteDatasetResponse> => Promise.reject(error));

            const { result } = renderProjectDatasetHook({ projectService, queryClient });

            act(() => {
                result.current.deleteDataset.mutate(mockDatasetIdentifier);
            });

            await waitFor(() => {
                expect(projectService.deleteDataset).toHaveBeenCalledWith(mockDatasetIdentifier);
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: error.message,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });
    });

    describe('useUpdateDataset', () => {
        const queryClient = new QueryClient();
        const mockInvalidateQueries = jest.fn();

        const mockDataset = getMockedDataset();

        queryClient.invalidateQueries = mockInvalidateQueries;

        it('mockInvalidateQueries is called when the call succeeds', async () => {
            projectService.updateDataset = jest.fn((): Promise<CreateDatasetResponse> => Promise.resolve(mockDataset));

            const { result } = renderProjectDatasetHook({ projectService, queryClient });

            act(() => {
                result.current.updateDataset.mutate({
                    datasetIdentifier: mockDatasetIdentifier,
                    updatedDataset: mockDataset,
                });
            });

            await waitFor(() => {
                expect(mockInvalidateQueries).toHaveBeenCalled();
                expect(mockAddNotification).not.toHaveBeenCalled();
                expect(projectService.updateDataset).toHaveBeenCalledWith(mockDatasetIdentifier, mockDataset);
            });
        });

        it('addNotification is called when the call fails', async () => {
            const error = { message: 'test' };

            projectService.updateDataset = jest.fn((): Promise<CreateDatasetResponse> => Promise.reject(error));

            const { result } = renderProjectDatasetHook({ projectService, queryClient });

            act(() => {
                result.current.updateDataset.mutate({
                    datasetIdentifier: mockDatasetIdentifier,
                    updatedDataset: mockDataset,
                });
            });

            await waitFor(() => {
                expect(projectService.updateDataset).toHaveBeenCalledWith(mockDatasetIdentifier, mockDataset);
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: error.message,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });
    });
});
