// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { getMockedProjectExportIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedProjectExportJob } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { JobState } from '../../jobs/jobs.const';
import { createInMemoryProjectService } from '../services/in-memory-project-service';
import { ProjectService } from '../services/project-service.interface';
import { useExportProjectStatusQuery } from './use-export-project-status.hook';
import { DOWNLOAD_STATUS_ERROR } from './use-export-project.hook';

const mockAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

describe('useExportProjectStatusQuery', () => {
    const mockData = getMockedProjectExportIdentifier({ workspaceId: '1', projectId: '4', exportProjectId: '2' });
    const mockOnSettled = jest.fn();
    const projectService = createInMemoryProjectService();

    const renderExportProjectStatusQueryHook = (params: { projectService: ProjectService }) => {
        return renderHookWithProviders(
            () =>
                useExportProjectStatusQuery({
                    isExporting: true,
                    variables: mockData,
                    onStart: jest.fn(),
                    onSettled: mockOnSettled,
                }),
            {
                providerProps: { projectService: params.projectService },
            }
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('exportProjectStatusMutation', () => {
        it('shows notification error with resolve error status', async () => {
            projectService.exportProjectStatus = jest.fn(() =>
                Promise.resolve(
                    getMockedProjectExportJob({
                        state: JobState.FAILED,
                        metadata: { downloadUrl: undefined, project: { id: 'id', name: 'name' } },
                    })
                )
            );
            renderExportProjectStatusQueryHook({ projectService });

            await waitFor(() => {
                expect(mockOnSettled).toHaveBeenCalled();
            });

            expect(projectService.exportProjectStatus).toHaveBeenCalledWith(mockData);
            expect(mockAddNotification).toHaveBeenCalledWith({
                message: DOWNLOAD_STATUS_ERROR,
                type: NOTIFICATION_TYPE.ERROR,
            });
        });

        it('does not show notification with resolve status different to error', async () => {
            projectService.exportProjectStatus = jest.fn(() =>
                Promise.resolve(
                    getMockedProjectExportJob({
                        state: JobState.RUNNING,
                        metadata: { downloadUrl: undefined, project: { id: 'id', name: 'name' } },
                    })
                )
            );
            const { result } = renderExportProjectStatusQueryHook({ projectService });

            await waitFor(() => {
                expect(result.current.status).toBe('success');
            });

            expect(mockOnSettled).not.toHaveBeenCalled();
            expect(projectService.exportProjectStatus).toHaveBeenCalledWith(mockData);
            expect(mockAddNotification).not.toHaveBeenCalled();
        });
    });
});
