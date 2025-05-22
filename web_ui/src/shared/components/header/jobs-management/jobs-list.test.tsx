// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useNavigate } from 'react-router-dom';

import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { SortDirection } from '../../../../core/shared/query-parameters';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { JobsList, JobsListProps } from './jobs-list.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: jest.fn(),
    useParams: () => ({ organizationId: 'organization-id', workspaceId: 'workspace_1' }),
}));

describe('jobs list', (): void => {
    const mockedJob: Job = getMockedJob();
    const mockedJobs = [
        mockedJob,
        { ...mockedJob, id: 'job-2', name: 'Train task job 2' },
        { ...mockedJob, id: 'job-3', name: 'Train task job 3' },
    ];

    const mockJobsListProps: JobsListProps = {
        jobs: mockedJobs,
        hasNextPage: false,
        fetchNextPage: jest.fn(),
        jobClickHandler: jest.fn(),
        isFetchingNextPage: false,
        isLoading: false,
        jobState: JobState.RUNNING,
        sortDirection: SortDirection.DESC,
        setSortDirection: jest.fn(),
    };

    const renderComponent = async (customProps?: Partial<JobsListProps>): Promise<void> => {
        render(<JobsList {...mockJobsListProps} {...customProps} />);
    };

    describe('render and navigation', () => {
        it('should properly render the list of jobs', async () => {
            await renderComponent();

            await waitFor(() => {
                const job1 = screen.queryByTestId('job-scheduler-job-1');
                expect(job1).toBeInTheDocument();
                expect(job1).toHaveAttribute('id', 'job-scheduler-job-1');
                expect(job1).toHaveTextContent('Train task job');

                const job2 = screen.queryByTestId('job-scheduler-job-2');
                expect(job2).toBeInTheDocument();
                expect(job2).toHaveAttribute('id', 'job-scheduler-job-2');
                expect(job2).toHaveTextContent('Train task job 2');

                const job3 = screen.queryByTestId('job-scheduler-job-3');
                expect(job3).toBeInTheDocument();
                expect(job3).toHaveAttribute('id', 'job-scheduler-job-3');
                expect(job3).toHaveTextContent('Train task job 3');
            });
        });

        it('should navigate to the models page on list item click when job is of train type', async () => {
            const mockNavigate = jest.fn();

            jest.mocked(useNavigate).mockImplementation(() => mockNavigate);

            await renderComponent();

            fireEvent.click(screen.getByTestId('job-scheduler-job-1-name'));
            expect(mockNavigate).toHaveBeenCalledWith(
                '/organizations/organization-id/workspaces/workspace_1/projects/123/models'
            );
        });

        it('should navigate to the tests page on list item click when job is of test type', async () => {
            const mockNavigate = jest.fn();

            jest.mocked(useNavigate).mockImplementation(() => mockNavigate);

            await renderComponent({
                jobState: JobState.RUNNING,
                jobs: [
                    getMockedJob({
                        type: JobType.TEST,
                        metadata: {
                            test: {
                                model: {
                                    id: 'id',
                                    optimizationType: 'BO',
                                    modelTemplateId: 'template-id',
                                    architectureName: 'template',
                                    hasExplainableAI: false,
                                    precision: [],
                                },
                                datasets: [{ id: 'dataset-id', name: 'dataset' }],
                            },
                            task: {
                                taskId: 'detection-task-id',
                            },
                            project: {
                                id: '123',
                                name: 'example project',
                            },
                        },
                    }),
                ],
            });

            fireEvent.click(screen.getByTestId('job-scheduler-job-1-name'));

            expect(mockNavigate).toHaveBeenCalledWith(
                '/organizations/organization-id/workspaces/workspace_1/projects/123/tests'
            );
        });
    });

    describe('should show correct message if there are no results', () => {
        it.each(Object.values(JobState))(
            'should show "There are no %o jobs" if there is nothing to show',
            async (jobState: JobState) => {
                await renderComponent({ jobState, jobs: [] });

                expect(screen.getByText(`There are no ${jobState} jobs`)).toBeInTheDocument();
            }
        );
    });
});
