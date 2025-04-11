// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { JobState, JobStepState } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { JobsListItemStatus } from './jobs-list-item-status.component';

const mockedJob = getMockedJob();

describe('jobs list item', (): void => {
    const renderComponent = async (job: Job = mockedJob, expanded = false): Promise<void> => {
        providersRender(<JobsListItemStatus job={job} expanded={expanded} />);
    };

    it('should properly render collapsed component', async (): Promise<void> => {
        await renderComponent();

        expect(screen.getByText('Test step (1 of 1)')).toBeInTheDocument();
        expect(screen.getByTestId('job-scheduler-job-1-progress')).toHaveTextContent('98%');
        expect(screen.getByTestId('job-scheduler-job-1-action-expand')).toHaveAttribute('aria-expanded', 'false');
        expect(screen.queryByTestId('job-scheduler-job-1-step-1')).not.toBeInTheDocument();
    });

    it('should properly render expanded component', async (): Promise<void> => {
        await renderComponent(mockedJob, true);

        expect(screen.queryByTestId('job-scheduler-job-1-progress')).not.toBeInTheDocument();
        expect(screen.getByTestId('job-scheduler-job-1-action-expand')).toHaveAttribute('aria-expanded', 'true');

        expect(screen.getByTestId('job-scheduler-job-1-step-1-test-step')).toBeInTheDocument();
        expect(screen.queryByTestId('job-scheduler-job-1-step-1-test-step-state-icon')).toBeInTheDocument();
        expect(screen.queryByTestId('job-scheduler-job-1-step-1-test-step-name')).toHaveTextContent(
            'Test step (1 of 1)'
        );
        expect(screen.queryByTestId('job-scheduler-job-1-step-1-test-step-progress')).toHaveTextContent('98%');
    });

    it('should render running step with highest index for progress in collapsed mode', async (): Promise<void> => {
        await renderComponent({
            ...mockedJob,
            steps: [
                ...mockedJob.steps,
                { ...mockedJob.steps[0], index: 2, stepName: 'Test step 2', state: JobStepState.RUNNING },
                { ...mockedJob.steps[0], index: 3, stepName: 'Test step 3', state: JobStepState.WAITING },
            ],
        });

        expect(screen.getByText('Test step 2 (2 of 3)')).toBeInTheDocument();
    });

    it('should properly render multiple steps in expanded mode', async (): Promise<void> => {
        await renderComponent(
            {
                ...mockedJob,
                steps: [
                    { ...mockedJob.steps[0], index: 1, stepName: 'Test step 1', state: JobStepState.RUNNING },
                    { ...mockedJob.steps[0], index: 2, stepName: 'Test step 2', state: JobStepState.WAITING },
                    { ...mockedJob.steps[0], index: 3, stepName: 'Test step 3', state: JobStepState.FINISHED },
                    { ...mockedJob.steps[0], index: 4, stepName: 'Test step 4', state: JobStepState.FAILED },
                    { ...mockedJob.steps[0], index: 5, stepName: 'Test step 5', state: JobStepState.CANCELLED },
                    { ...mockedJob.steps[0], index: 6, stepName: 'Test step 6', state: JobStepState.SKIPPED },
                ],
            },
            true
        );

        expect(screen.getByTestId('job-scheduler-job-1-step-1-test-step-1-name')).toHaveTextContent(
            'Test step 1 (1 of 6)'
        );
        expect(screen.getByTestId('job-scheduler-job-1-step-2-test-step-2-name')).toHaveTextContent(
            'Test step 2 (2 of 6)'
        );
        expect(screen.getByTestId('job-scheduler-job-1-step-3-test-step-3-name')).toHaveTextContent(
            'Test step 3 (3 of 6)'
        );
        expect(screen.getByTestId('job-scheduler-job-1-step-4-test-step-4-name')).toHaveTextContent(
            'Test step 4 (4 of 6)'
        );
        expect(screen.getByTestId('job-scheduler-job-1-step-5-test-step-5-name')).toHaveTextContent(
            'Test step 5 (5 of 6)'
        );
        expect(screen.getByTestId('job-scheduler-job-1-step-6-test-step-6-name')).toHaveTextContent(
            'Test step 6 (6 of 6)'
        );
    });

    it("displays job duration as sum of the job steps' durations for finished job", () => {
        const job = getMockedJob({
            state: JobState.FINISHED,
            endTime: '2025-02-11T08:50:58.354000+00:00',
            startTime: '2025-02-11T08:48:25.725000+00:00',
            steps: [
                {
                    message: 'Training data prepared',
                    index: 1,
                    progress: 100,
                    state: JobStepState.FINISHED,
                    duration: 11.678,
                    stepName: 'Prepare training data',
                },
                {
                    message: 'Model is trained',
                    index: 2,
                    progress: 100,
                    state: JobStepState.FINISHED,
                    duration: 14.002,
                    stepName: 'Model training',
                },
                {
                    message: 'Model is evaluated and inference is finished',
                    index: 3,
                    progress: 100,
                    state: JobStepState.FINISHED,
                    duration: 22.029,
                    stepName: 'Model evaluation and inference',
                },
            ],
        });

        renderComponent(job);

        expect(screen.getByText('Completed in: 2 min, 32 sec')).toBeInTheDocument();
    });

    it.each([JobState.SCHEDULED, JobState.FAILED, JobState.RUNNING, JobState.CANCELLED])(
        'does not display job duration for jobs other than FINISHED',
        (jobState) => {
            const job = getMockedJob({
                state: jobState,
                endTime: '2025-02-11T08:50:58.354000+00:00',
                startTime: '2025-02-11T08:48:25.725000+00:00',
                steps: [
                    {
                        message: 'Training data prepared',
                        index: 1,
                        progress: 100,
                        state: JobStepState.FINISHED,
                        duration: 11.678,
                        stepName: 'Prepare training data',
                    },
                    {
                        message: 'Model is trained',
                        index: 2,
                        progress: 100,
                        state: JobStepState.FINISHED,
                        duration: 14.002,
                        stepName: 'Model training',
                    },
                    {
                        message: 'Model is evaluated and inference is finished',
                        index: 3,
                        progress: 100,
                        state: JobStepState.FINISHED,
                        duration: 22.029,
                        stepName: 'Model evaluation and inference',
                    },
                ],
            });

            renderComponent(job);

            expect(screen.queryByText(/Completed in/)).not.toBeInTheDocument();
        }
    );
});
