// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { JobCancellationWarning } from './jobs-cancellation-warning.component';

describe('jobs dialog', (): void => {
    beforeEach((): void => {
        jest.clearAllMocks();
    });

    const renderComponent = async ({
        totalCreditsConsumed,
        isLoseCreditsContentShown,
        setIsOpen = jest.fn(),
        onPrimaryAction = jest.fn(),
    }: {
        totalCreditsConsumed: number;
        isLoseCreditsContentShown: boolean;
        setIsOpen?: jest.Mock;
        onPrimaryAction?: jest.Mock;
    }) => {
        render(
            <JobCancellationWarning
                isOpen
                jobName='Training job'
                shouldShowLostCreditsContent={isLoseCreditsContentShown}
                totalCreditsConsumed={totalCreditsConsumed}
                setIsOpen={setIsOpen}
                onPrimaryAction={onPrimaryAction}
                isPrimaryActionDisabled={false}
            />
        );
    };

    it('render total consumed credits and calls onPrimary action', () => {
        const onPrimaryAction = jest.fn();
        renderComponent({
            isLoseCreditsContentShown: true,
            onPrimaryAction,
            totalCreditsConsumed: 20,
        });

        expect(
            screen.getByText(/Are you sure you want to cancel job "Training job" and lose 20 credits?/i)
        ).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: 'Cancel job' }));

        expect(onPrimaryAction).toHaveBeenCalled();
    });

    it('close modal', () => {
        const setIsOpen = jest.fn();
        renderComponent({
            isLoseCreditsContentShown: true,
            setIsOpen,
            totalCreditsConsumed: 20,
        });

        fireEvent.click(screen.getByRole('button', { name: 'Close cancel job dialog' }));

        expect(setIsOpen).toHaveBeenCalledWith(false);
    });
});
