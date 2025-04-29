// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { ApplicationServicesProvider } from '../../services/application-services-provider.component';
import { ProjectImport, ProjectImportIdentifier } from '../project.interface';
import { createInMemoryProjectService } from '../services/in-memory-project-service';
import { ProjectService } from '../services/project-service.interface';
import { useImportProject } from './use-import-project.hook';

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

const renderImportProjectHook = (params: { projectService: ProjectService }) => {
    return renderHook(() => useImportProject().useImportProjectMutation(), {
        wrapper: ({ children }) => wrapper({ children, projectService: params.projectService }),
    });
};

describe('useImportProject', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('importProjectMutation', () => {
        const mockData: ProjectImportIdentifier = {
            workspaceId: '123',
            importProjectId: '1234-name',
            organizationId: 'organization-id',
        };

        it('shows notification error with promise rejection', async () => {
            const error = { message: 'test' };
            const projectService = createInMemoryProjectService();

            projectService.importProject = jest.fn((): Promise<ProjectImport> => Promise.reject(error));

            const { result } = renderImportProjectHook({ projectService });

            act(() => {
                result.current.mutate({
                    identifier: mockData,
                    options: {
                        skipSignatureVerification: false,
                        keepOriginalDates: false,
                        projectName: 'Test project',
                    },
                });
            });

            await waitFor(() => {
                expect(projectService.importProject).toHaveBeenCalledWith(mockData, {
                    skipSignatureVerification: false,
                    keepOriginalDates: false,
                    projectName: 'Test project',
                });
            });

            expect(mockAddNotification).toHaveBeenCalledWith({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        });

        it('returns status url and import project id (file id) on success', async () => {
            const projectService = createInMemoryProjectService();

            const { result } = renderImportProjectHook({ projectService });

            act(() => {
                result.current.mutate({
                    identifier: mockData,
                    options: { skipSignatureVerification: false, keepOriginalDates: false, projectName: '' },
                });
            });

            await waitFor(() => {
                expect(result.current.data).toEqual({ importProjectId: expect.anything() });
            });
        });
    });
});
