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

import { fireEvent, screen } from '@testing-library/react';

import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { getMockedJob } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { JobsDiscardAction } from './jobs-discard-action.component';
import { DISCARD_TYPE } from './utils';

const mockedJob: Job = getMockedJob({
    id: 'mocked-job-id',
    cost: { consumed: [{ amount: 20, consumingDate: '123', unit: 'image' }], leaseId: '1', requests: [] },
});
const mockUseDeleteJob = {
    mutate: jest.fn(),
    isLoading: false,
    isSuccess: false,
};
const mockUseCancelJob = {
    mutate: jest.fn(),
    isLoading: false,
    isSuccess: false,
};

describe('jobs discard action', (): void => {
    const renderComponent = async ({
        discardType,
        useDeleteJob = mockUseDeleteJob,
        useCancelJob = mockUseCancelJob,
        job = mockedJob,
        creditSystemFlag = false,
    }: {
        discardType: DISCARD_TYPE;
        useDeleteJob?: typeof mockUseDeleteJob;
        useCancelJob?: typeof mockUseCancelJob;
        job?: Job;
        creditSystemFlag?: boolean;
    }) => {
        return render(
            <JobsDiscardAction
                job={job}
                discardType={discardType}
                // @ts-expect-error we dont need to match types as we're using mocks
                useCancelJob={useCancelJob}
                // @ts-expect-error we dont need to match types as we're using mocks
                useDeleteJob={useDeleteJob}
            />,
            { featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: creditSystemFlag } }
        );
    };

    it('should render "Delete" action link on DISCARD_TYPE.DELETE', async (): Promise<void> => {
        await renderComponent({ discardType: DISCARD_TYPE.DELETE });

        expect(screen.getByText('trash.svg')).toBeVisible();
        expect(screen.getByTestId(`job-scheduler-${mockedJob.id}-action-delete`)).toBeVisible();
    });

    it('should render "Cancel" action link on DISCARD_TYPE.CANCEL', async (): Promise<void> => {
        await renderComponent({ discardType: DISCARD_TYPE.CANCEL });

        expect(screen.getByRole('button', { name: 'Cancel' })).toBeVisible();
        expect(screen.getByTestId(`job-scheduler-${mockedJob.id}-action-cancel`)).toBeVisible();
    });

    it('should render confirmation dialog on press "Cancel"', async (): Promise<void> => {
        const mockedJobCost = getMockedJob({
            id: 'mocked-job-id',
            cost: {
                leaseId: '123',
                requests: [],
                consumed: [{ amount: 20, consumingDate: '123', unit: 'image' }],
            },
        });
        await renderComponent({ discardType: DISCARD_TYPE.CANCEL, job: mockedJobCost, creditSystemFlag: true });

        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

        expect(
            screen.getByText(/Are you sure you want to cancel job "Train task job" and lose 20 credits/i)
        ).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Cancel job' }));

        expect(mockUseCancelJob.mutate).toHaveBeenCalledWith(mockedJob.id);
    });

    it('render credit warning dialog on press "Cancel"', async (): Promise<void> => {
        await renderComponent({ discardType: DISCARD_TYPE.CANCEL, job: { ...mockedJob, name: 'mocked job' } });

        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

        expect(screen.getByRole('alertdialog')).toBeVisible();

        expect(screen.getByRole('heading', { name: 'Cancel job' })).toBeInTheDocument();
        expect(screen.getByText(/Are you sure you want to cancel job "mocked job"?/)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Close cancel job dialog' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Cancel job' })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Cancel job' }));

        expect(mockUseCancelJob.mutate).toHaveBeenCalledWith(mockedJob.id);
    });

    it('should render confirmation dialog on press "Delete"', async (): Promise<void> => {
        await renderComponent({ discardType: DISCARD_TYPE.DELETE });

        fireEvent.click(screen.getByLabelText('Delete job'));

        expect(screen.getByRole('alertdialog')).toBeVisible();

        expect(screen.getByRole('heading', { name: 'Delete job' })).toBeInTheDocument();
        expect(screen.getByText('Are you sure you want to delete job "Train task job"?')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Close delete job dialog' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Delete job' })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Delete job' }));

        expect(mockUseDeleteJob.mutate).toHaveBeenCalledWith(mockedJob.id);
    });

    it('should render a loader and disable "Delete" action link if delete event is in progress', async (): Promise<void> => {
        const mockUseDeleteJobLoading = {
            mutate: jest.fn(),
            isLoading: true,
            isSuccess: false,
        };
        await renderComponent({ discardType: DISCARD_TYPE.DELETE, useDeleteJob: mockUseDeleteJobLoading });

        expect(screen.getByTestId(`job-scheduler-${mockedJob.id}-action-delete`)).toBeVisible();
    });

    it('should render a loader if cancel event is in progress', async (): Promise<void> => {
        const mockUseCancelJobLoading = {
            mutate: jest.fn(),
            isLoading: true,
            isSuccess: false,
        };

        await renderComponent({ discardType: DISCARD_TYPE.CANCEL, useDeleteJob: mockUseCancelJobLoading });

        expect(screen.getByTestId(`job-scheduler-${mockedJob.id}-action-cancel`)).toBeVisible();
    });

    it('renders the normal "cancel" dialog if the credits consumed equal to zero', async (): Promise<void> => {
        await renderComponent({
            discardType: DISCARD_TYPE.CANCEL,
            creditSystemFlag: true,
            job: getMockedJob({
                id: 'mocked-job-id',
                type: JobType.TRAIN,
                cost: {
                    leaseId: '123',
                    requests: [],
                    consumed: [{ amount: 0, consumingDate: '123', unit: 'image' }],
                },
            }),
        });

        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

        expect(screen.queryByText(/Are you sure you want to cancel job "[\w\s]*"?/)).toBeInTheDocument();
    });

    it('renders the "job cancellation warning" dialog if the credits consumed are bigger than zero', async (): Promise<void> => {
        await renderComponent({
            discardType: DISCARD_TYPE.CANCEL,
            creditSystemFlag: true,
            job: getMockedJob({
                type: JobType.TRAIN,
                cost: {
                    leaseId: '123',
                    requests: [],
                    consumed: [{ amount: 5, consumingDate: '123', unit: 'image' }],
                },
            }),
        });

        fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

        expect(
            screen.queryByText(/Are you sure you want to cancel job "[\w\s]*" and lose 5 credits?/)
        ).toBeInTheDocument();
    });

    it('should be disabled when the job is running and is not cancellable', async (): Promise<void> => {
        await renderComponent({
            discardType: DISCARD_TYPE.CANCEL,
            job: getMockedJob({
                id: 'mocked-job-id',
                state: JobState.RUNNING,
                cancellationInfo: {
                    isCancellable: false,
                    isCancelled: false,
                    userUId: null,
                    cancelTime: null,
                },
            }),
        });

        const cancelButton = screen.getByRole('button', { name: 'Cancel' });

        await checkTooltip(cancelButton, 'For data consistency reasons, this job cannot be cancelled.');
        expect(cancelButton).toBeDisabled();
    });
});
