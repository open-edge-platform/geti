// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { getMockedProjectImportIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { ExportStatusStateDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';
import { ProjectImportStatus } from '../project.interface';
import { createInMemoryProjectService } from '../services/in-memory-project-service';
import { ProjectService } from '../services/project-service.interface';
import { useImportProjectStatusQuery } from './use-import-project-status.hook';
import { IMPORT_STATUS_ERROR } from './use-import-project.hook';

const mockAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

const projectService = createInMemoryProjectService();
describe('useImportProjectStatusQuery', () => {
    const projectImportIdentifier = getMockedProjectImportIdentifier({ workspaceId: '123', importProjectId: '321' });
    const mockOnDone = jest.fn(() => Promise.resolve());
    const mockOnError = jest.fn();

    const renderImportProjectStatusQuery = (params: { projectService: ProjectService }) => {
        return renderHookWithProviders(
            () =>
                useImportProjectStatusQuery({
                    projectImportIdentifier,
                    onDone: mockOnDone,
                    onError: mockOnError,
                }),
            {
                providerProps: { projectService: params.projectService },
            }
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('importProjectStatusQuery', () => {
        it('shows notification error with resolve error status', async () => {
            projectService.getImportProjectStatus = jest.fn(
                async (): Promise<ProjectImportStatus> =>
                    Promise.resolve({
                        progress: -1,
                        projectId: null,
                        state: ExportStatusStateDTO.ERROR,
                    })
            );

            renderImportProjectStatusQuery({ projectService });

            await waitFor(() => {
                expect(projectService.getImportProjectStatus).toHaveBeenCalledWith(projectImportIdentifier);
                expect(mockOnError).toHaveBeenCalled();
            });

            expect(mockAddNotification).toHaveBeenCalledWith({
                message: IMPORT_STATUS_ERROR,
                type: NOTIFICATION_TYPE.ERROR,
            });
        });

        it('does not show notification with resolve status different to error', async () => {
            projectService.getImportProjectStatus = jest.fn(
                async (): Promise<ProjectImportStatus> =>
                    Promise.resolve({
                        progress: -1,
                        projectId: null,
                        state: ExportStatusStateDTO.EXPORTING,
                    })
            );

            renderImportProjectStatusQuery({ projectService });

            await waitFor(() => {
                expect(projectService.getImportProjectStatus).toHaveBeenCalledWith(projectImportIdentifier);
            });

            expect(mockAddNotification).not.toHaveBeenCalled();
        });

        it('calls onDone', async () => {
            projectService.getImportProjectStatus = jest.fn(
                async (): Promise<ProjectImportStatus> =>
                    Promise.resolve({
                        progress: -1,
                        projectId: null,
                        state: ExportStatusStateDTO.DONE,
                    })
            );

            renderImportProjectStatusQuery({ projectService });

            await waitFor(() => {
                expect(projectService.getImportProjectStatus).toHaveBeenCalledWith(projectImportIdentifier);
                expect(mockOnDone).toHaveBeenCalled();
            });

            expect(mockAddNotification).not.toHaveBeenCalled();
        });
    });
});
