// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { WorkspaceIdentifier } from '@geti/core/src/workspaces/services/workspaces.interface';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import { JobState, JobStepState } from '../../../../../../../core/jobs/jobs.const';
import { JobProjectExportStatus } from '../../../../../../../core/jobs/jobs.interface';
import { createInMemoryJobsService } from '../../../../../../../core/jobs/services/in-memory-jobs-service';
import { createInMemoryProjectService } from '../../../../../../../core/projects/services/in-memory-project-service';
import * as sharedUtils from '../../../../../../../shared/utils';
import { getDownloadNotificationMessage } from '../../../../../../../shared/utils';
import { getMockedProjectExportJob } from '../../../../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender } from '../../../../../../../test-utils/required-providers-render';
import { ProjectExportStatus } from './project-export-status.component';

describe('ProjectExportStatus', () => {
    afterEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    const render = ({
        isExporting = true,
        setIsExporting = jest.fn(),
        job = getMockedProjectExportJob(),
        onResetProjectExport = jest.fn(),
        onCancelJob = jest.fn(),
    }: {
        isExporting?: boolean;
        setIsExporting?: Dispatch<SetStateAction<boolean>>;
        onResetProjectExport?: () => void;
        job?: JobProjectExportStatus;
        onCancelJob?: (workspaceIdentifier: WorkspaceIdentifier, jobId: string) => Promise<string>;
    } = {}) => {
        const projectService = createInMemoryProjectService();
        projectService.exportProjectStatus = jest.fn().mockResolvedValue(job);

        const jobsService = createInMemoryJobsService();
        jobsService.cancelJob = onCancelJob;

        return providersRender(
            <ProjectExportStatus
                projectId={'project-id'}
                isExporting={isExporting}
                setIsExporting={setIsExporting}
                workspaceIdentifier={{ organizationId: 'org-id', workspaceId: 'workspace-id' }}
                exportProjectMutationIdentifier={{
                    organizationId: 'org-id',
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                    exportProjectId: 'project-id',
                }}
                onResetProjectExport={onResetProjectExport}
            />,
            { services: { projectService, jobsService } }
        );
    };

    it("doesn't display anything when there is no exporting", () => {
        render({ isExporting: false });

        expect(screen.queryByTestId('project-id-exporting-details-id')).not.toBeInTheDocument();
    });

    it('displays exporting details when the export is in progress', async () => {
        const jobInProgress = getMockedProjectExportJob({
            state: JobState.RUNNING,
            steps: [
                {
                    state: JobStepState.RUNNING,
                    stepName: 'Exporting project',
                    progress: 50,
                    index: 1,
                    message: 'Preparing',
                },
            ],
        });
        const mockSetIsExporting = jest.fn();
        const mockOnResetProjectExport = jest.fn();
        const mockOnCancelJob = jest.fn();

        render({
            isExporting: true,
            job: jobInProgress,
            setIsExporting: mockSetIsExporting,
            onCancelJob: mockOnCancelJob,
            onResetProjectExport: mockOnResetProjectExport,
        });

        expect(await screen.findByTestId('project-id-exporting-details-id')).toBeInTheDocument();
        expect(await screen.findByTestId('project-id-export-project-progress-state-icon')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'cancel export' })).toBeInTheDocument();
        expect(screen.getByText('Exporting project: Preparing')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Download exported project' })).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'cancel export' }));

        expect(mockSetIsExporting).toHaveBeenCalledWith(false);

        await waitFor(() => {
            expect(mockOnCancelJob).toHaveBeenCalledWith(
                {
                    organizationId: 'org-id',
                    workspaceId: 'workspace-id',
                },
                'project-id'
            );
            expect(mockOnResetProjectExport).toHaveBeenCalled();
        });

        expect(mockOnResetProjectExport).toHaveBeenCalled();
    });

    it('displays "download" button and "close" button when the export is completed', async () => {
        const finishedJob = getMockedProjectExportJob({
            state: JobState.FINISHED,
            steps: [
                {
                    state: JobStepState.FINISHED,
                    stepName: 'Exporting project',
                    progress: 100,
                    index: 1,
                    message: 'Finished',
                },
            ],
        });

        const downloadFileSpy = jest.spyOn(sharedUtils, 'downloadFile');

        render({
            isExporting: true,
            job: finishedJob,
        });

        expect(await screen.findByTestId('project-id-exporting-details-id')).toBeInTheDocument();
        expect(await screen.findByTestId('project-id-export-project-progress-state-icon')).toBeInTheDocument();

        expect(screen.getByRole('button', { name: 'close' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Download exported project' })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Download exported project' }));

        expect(downloadFileSpy).toHaveBeenCalledWith(expect.any(String), 'intel_geti_project-id.zip');

        expect(await screen.findByText(getDownloadNotificationMessage('project'))).toBeInTheDocument();
    });
});
