// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { ApplicationServicesProvider } from '@geti/core/src/services/application-services-provider.component';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { getMockedProjectExportIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { ProjectExport } from '../project.interface';
import { createInMemoryProjectService } from '../services/in-memory-project-service';
import { ProjectService } from '../services/project-service.interface';
import { useExportProject } from './use-export-project.hook';

const mockAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

const wrapper = ({ children, projectService }: { children?: ReactNode; projectService: ProjectService }) => {
    const queryClient = new QueryClient();
    return (
        <ApplicationServicesProvider useInMemoryEnvironment projectService={projectService}>
            <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        </ApplicationServicesProvider>
    );
};

const projectService = createInMemoryProjectService();
describe('useExportProject', () => {
    const mockData = getMockedProjectExportIdentifier({ workspaceId: '1', projectId: '4', exportProjectId: '2' });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('exportProjectMutation', () => {
        it('shows notification error with promise rejection', async () => {
            const error = { message: 'test' };
            projectService.exportProject = jest.fn((): Promise<ProjectExport> => Promise.reject(error));

            const { result } = renderHook(() => useExportProject(), {
                wrapper: ({ children }) => wrapper({ children, projectService }),
            });

            act(() => {
                result.current.exportProjectMutation.mutate(mockData);
            });

            await waitFor(() => {
                expect(projectService.exportProject).toHaveBeenCalledWith(mockData);
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: error.message,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });
    });
});
