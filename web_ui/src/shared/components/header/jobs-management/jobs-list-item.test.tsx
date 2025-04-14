// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { getMockedDatasetExportJob, getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { onHoverTooltip } from '../../../../test-utils/utils';
import { downloadFile } from '../../../utils';
import { JobsListItem } from './jobs-list-item.component';
import { DISCARD_TYPE } from './utils';

const mockedMetadata = {
    task: {
        modelArchitecture: 'YoloV4',
        name: 'Detection',
        datasetStorageId: 'dataset-storage-id',
        modelTemplateId: 'template-id',
        taskId: 'detection-task-id',
        scores: [{ score: 98, taskId: 'detection-task-id' }],
    },
    project: {
        id: '123',
        name: 'example project',
    },
    trainedModel: {
        modelId: 'model-id',
    },
};
const mockedJob = getMockedJob({
    metadata: mockedMetadata,
    type: JobType.TRAIN,
    cost: {
        leaseId: '123',
        requests: [{ amount: 20, unit: 'image' }],
        consumed: [{ amount: 10, unit: 'image', consumingDate: '10-10-10' }],
    },
});

const baseCheck = (): void => {
    expect(screen.getByTestId('job-scheduler-job-1')).toBeInTheDocument();
    expect(screen.getByTestId('job-scheduler-job-1')).toHaveTextContent('Train task job');
    expect(screen.getByTestId('job-scheduler-job-1-action-delete')).toHaveTextContent('trash.svg');

    expect(screen.getByText(`Project: ${mockedMetadata.project.name}`)).toBeInTheDocument();
    expect(screen.getByText(`Architecture: ${mockedMetadata.task.modelArchitecture}`)).toBeInTheDocument();
    expect(screen.getByText(`Task: ${mockedMetadata.task.name}`)).toBeInTheDocument();
    expect(screen.getByText('Created: 06:17:43, 10 Aug 23')).toBeInTheDocument();
    expect(screen.queryByText('Cost: 20 credits')).not.toBeInTheDocument();

    expect(screen.getByText('Test step (1 of 1)')).toBeInTheDocument();
};

jest.mock('../../../utils', () => ({
    ...jest.requireActual('../../../utils'),
    downloadFile: jest.fn(),
}));

jest.mock('../../../../core/jobs/hooks/use-jobs.hook', () => ({
    ...jest.requireActual('../../../../core/jobs/hooks/use-jobs.hook'),
    useJobs: jest.fn(() => ({
        useDeleteJob: {
            mutate: jest.fn(),
            isLoading: false,
        },
        useCancelJob: {
            mutate: jest.fn(),
            isLoading: false,
        },
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

describe('jobs list item', (): void => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    const renderComponent = async ({
        expanded = false,
        job = mockedJob,
        discardType = DISCARD_TYPE.DELETE,
        enableCreditSystem = false,
    }: {
        expanded?: boolean;
        job?: Job;
        discardType?: DISCARD_TYPE;
        enableCreditSystem?: boolean;
    }): Promise<void> => {
        providersRender(
            <JobsListItem
                job={{ ...job, creationTime: '2023-08-10T06:17:43.849000+00:00' }}
                expanded={expanded}
                discardType={discardType}
            />,
            {
                featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: enableCreditSystem },
            }
        );
    };

    it('should properly render collapsed component', async (): Promise<void> => {
        await renderComponent({});

        baseCheck();

        expect(screen.getByTestId('job-scheduler-job-1-progress')).toHaveTextContent('98%');
        expect(screen.getByTestId('job-scheduler-job-1-action-expand')).toHaveAttribute('aria-expanded', 'false');
        expect(screen.queryByTestId('job-scheduler-job-1-step-1-meta')).not.toBeInTheDocument();
    });

    it('should properly render expanded component', async (): Promise<void> => {
        await renderComponent({ expanded: true });

        expect(screen.queryByTestId('job-scheduler-job-1-progress')).not.toBeInTheDocument();
        expect(screen.getByTestId('job-scheduler-job-1-action-expand')).toHaveAttribute('aria-expanded', 'true');

        expect(screen.getByTestId('job-scheduler-job-1-step-1-test-step')).toBeInTheDocument();
        expect(screen.queryByTestId('job-scheduler-job-1-step-1-test-step-state-icon')).toBeInTheDocument();
        expect(screen.queryByTestId('job-scheduler-job-1-step-1-test-step-name')).toHaveTextContent(
            'Test step (1 of 1)'
        );
        expect(screen.queryByTestId('job-scheduler-job-1-step-1-test-step-progress')).toHaveTextContent('98%');
    });

    it('render download button', async (): Promise<void> => {
        const downloadUrl = '/api/url-test';

        await renderComponent({
            job: getMockedDatasetExportJob({
                state: JobState.FINISHED,
                metadata: { downloadUrl, project: { id: 'some-id', name: 'some-name' } },
            }),
        });

        fireEvent.click(screen.getByRole('button', { name: 'download dataset' }));

        expect(downloadFile).toBeCalledWith(downloadUrl, 'export_dataset');
    });

    it('correctly downloads project', async (): Promise<void> => {
        const downloadUrl = '/api/url-test';

        await renderComponent({
            job: getMockedJob({
                state: JobState.FINISHED,
                metadata: {
                    downloadUrl,
                    project: { id: 'some-id', name: 'some name' },
                    includePersonalData: false,
                    includeModels: false,
                },
                type: JobType.EXPORT_PROJECT,
            }),
        });

        fireEvent.click(screen.getByRole('button', { name: 'download project' }));

        expect(downloadFile).toBeCalledWith(downloadUrl, 'some_name.zip');
    });

    it('should properly render a skeleton loader if the user is cancelling or deleting the job', async (): Promise<void> => {
        jest.mocked(useJobs).mockImplementationOnce(() => ({
            // @ts-expect-error partial mock
            useDeleteJob: {
                isPending: true,
            },
        }));

        await renderComponent({});

        expect(screen.queryByTestId('job-item-loader-list')).toBeInTheDocument();
    });

    it('should properly render metadata', async (): Promise<void> => {
        const downloadUrl = '/url-test';

        await renderComponent({
            job: getMockedDatasetExportJob({
                state: JobState.FINISHED,
                metadata: { downloadUrl, project: { id: 'some-id', name: 'some-name' } },
            }),
        });

        expect(screen.getByText('Project: some-name')).toBeInTheDocument();
    });

    it('should render cost section if FF is on', async () => {
        jest.useFakeTimers();
        await renderComponent({ enableCreditSystem: true });

        expect(screen.getByText('Cost: 20 credits')).toBeVisible();
        onHoverTooltip(screen.getByText('Cost: 20 credits'));
        jest.advanceTimersByTime(750);
        expect(await screen.findByText('Credits requested: 20', { exact: false })).toBeVisible();
        expect(screen.getByText('Credits consumed: 10', { exact: false })).toBeVisible();
    });
});
