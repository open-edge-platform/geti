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

import { render, screen } from '@testing-library/react';

import { JobStepState } from '../../../../core/jobs/jobs.const';
import { JobStep } from '../../../../core/jobs/jobs.interface';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { JobsListItemDetailedProgress } from './jobs-list-item-progress.component';

const mockedStep: JobStep = {
    message: 'Train data retrieved',
    index: 1,
    progress: 50,
    state: JobStepState.RUNNING,
    stepName: 'Retrieve train data',
};

describe('jobs list item progress', () => {
    const renderComponent = (stepProps: Partial<JobStep> = {}): void => {
        render(<JobsListItemDetailedProgress job={getMockedJob()} step={{ ...mockedStep, ...stepProps }} />);
    };

    it.each([
        {
            state: JobStepState.RUNNING,
            stateStr: JobStepState.RUNNING.toUpperCase(),
            icon: 'loader.svg',
        },
        {
            state: JobStepState.FINISHED,
            stateStr: JobStepState.FINISHED.toUpperCase(),
            icon: 'check-circle-outlined.svg',
        },
        {
            state: JobStepState.SKIPPED,
            stateStr: JobStepState.SKIPPED.toUpperCase(),
            icon: 'skipped-icon.svg',
        },
        {
            state: JobStepState.FAILED,
            stateStr: JobStepState.FAILED.toUpperCase(),
            icon: 'exclamation-circle-outlined.svg',
        },
        {
            state: JobStepState.CANCELLED,
            stateStr: JobStepState.CANCELLED.toUpperCase(),
            icon: 'canceled-icon.svg',
        },
        {
            state: JobStepState.WAITING,
            stateStr: JobStepState.WAITING.toUpperCase(),
            icon: 'waiting-icon.svg',
        },
    ])(
        'should show "$icon" icon and step name for step in state "$stateStr"',
        async ({ state, icon }): Promise<void> => {
            await renderComponent({ state });

            if (state === JobStepState.RUNNING) {
                expect(screen.queryByRole('progressbar', { name: 'Loading...' })).toBeVisible();
            } else {
                expect(screen.queryByText(String(icon))).toBeVisible();
            }
        }
    );

    it.each([
        {
            state: JobStepState.RUNNING,
            stateStr: JobStepState.RUNNING.toUpperCase(),
            message: 'test message',
        },
        {
            state: JobStepState.FINISHED,
            stateStr: JobStepState.FINISHED.toUpperCase(),
            message: 'test message',
        },
        {
            state: JobStepState.SKIPPED,
            stateStr: JobStepState.SKIPPED.toUpperCase(),
            message: '',
        },
        {
            state: JobStepState.FAILED,
            stateStr: JobStepState.FAILED.toUpperCase(),
            message: '',
        },
        {
            state: JobStepState.CANCELLED,
            stateStr: JobStepState.CANCELLED.toUpperCase(),
            message: 'test message',
        },
        {
            state: JobStepState.WAITING,
            stateStr: JobStepState.WAITING.toUpperCase(),
            message: 'test message',
        },
    ])('shows name and message for step in state "$stateStr"', async ({ state, message }): Promise<void> => {
        await renderComponent({ state, message });

        if (state !== JobStepState.FAILED && state !== JobStepState.SKIPPED) {
            expect(screen.getByText(`Retrieve train data (1 of 1): ${message}`)).toBeVisible();
        } else {
            expect(screen.getByText(`Retrieve train data (1 of 1)`)).toBeVisible();
        }
    });

    it.each([
        {
            state: JobStepState.RUNNING,
            stateStr: JobStepState.RUNNING.toUpperCase(),
            result: '72%',
        },
        {
            state: JobStepState.FINISHED,
            stateStr: JobStepState.FINISHED.toUpperCase(),
            result: '100%',
        },
        {
            state: JobStepState.SKIPPED,
            stateStr: JobStepState.SKIPPED.toUpperCase(),
            result: 'Skipped',
        },
        {
            state: JobStepState.FAILED,
            stateStr: JobStepState.FAILED.toUpperCase(),
            result: 'Failed',
        },
        {
            state: JobStepState.CANCELLED,
            stateStr: JobStepState.CANCELLED.toUpperCase(),
            result: 'Cancelled',
        },
        {
            state: JobStepState.WAITING,
            stateStr: JobStepState.WAITING.toUpperCase(),
            result: 'Waiting...',
        },
    ])(
        'should show "$result" as progress status for step in state "$stateStr"',
        async ({ state, result }): Promise<void> => {
            await renderComponent({ state, progress: state === JobStepState.FINISHED ? 100 : 72 });
            expect(screen.getByTestId('job-scheduler-job-1-step-1-retrieve-train-data-progress')).toHaveTextContent(
                result
            );
        }
    );

    it.each([
        { state: JobStepState.RUNNING, result: true, stateStr: JobStepState.RUNNING.toUpperCase(), resultStr: 'show' },
        {
            state: JobStepState.FINISHED,
            result: true,
            stateStr: JobStepState.FINISHED.toUpperCase(),
            resultStr: 'show',
        },
        {
            state: JobStepState.SKIPPED,
            result: false,
            stateStr: JobStepState.SKIPPED.toUpperCase(),
            resultStr: 'not show',
        },
        {
            state: JobStepState.FAILED,
            result: false,
            stateStr: JobStepState.FAILED.toUpperCase(),
            resultStr: 'not show',
        },
        {
            state: JobStepState.CANCELLED,
            result: true,
            stateStr: JobStepState.CANCELLED.toUpperCase(),
            resultStr: 'show',
        },
        {
            state: JobStepState.WAITING,
            result: true,
            stateStr: JobStepState.WAITING.toUpperCase(),
            resultStr: 'show',
        },
    ])('should $resultStr progress bar for step in state "$stateStr"', async ({ state, result }): Promise<void> => {
        await renderComponent({ state });
        expect(Boolean(screen.queryByTestId('thin-progress-bar'))).toBe(result);
    });

    it.each([
        {
            state: JobStepState.RUNNING,
            result: false,
            stateStr: JobStepState.RUNNING.toUpperCase(),
            resultStr: 'not show',
        },
        {
            state: JobStepState.FINISHED,
            result: false,
            stateStr: JobStepState.FINISHED.toUpperCase(),
            resultStr: 'not show',
        },
        {
            state: JobStepState.SKIPPED,
            result: true,
            stateStr: JobStepState.SKIPPED.toUpperCase(),
            resultStr: 'show',
        },
        {
            state: JobStepState.FAILED,
            result: true,
            stateStr: JobStepState.FAILED.toUpperCase(),
            resultStr: 'show',
        },
        {
            state: JobStepState.CANCELLED,
            result: false,
            stateStr: JobStepState.CANCELLED.toUpperCase(),
            resultStr: 'not show',
        },
        {
            state: JobStepState.WAITING,
            result: false,
            stateStr: JobStepState.WAITING.toUpperCase(),
            resultStr: 'not show',
        },
    ])('should $resultStr root cause description for step in state "$stateStr"', ({ state, result }) => {
        renderComponent({
            message: result ? 'Root cause description' : '',
            state,
        });
        expect(Boolean(screen.queryByTestId('job-scheduler-job-1-step-1-retrieve-train-data-message'))).toBe(result);
        if (result) {
            expect(screen.queryByTestId('job-scheduler-job-1-step-1-retrieve-train-data-message')).toHaveTextContent(
                'Root cause description'
            );
        }
    });
});
