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

import { getLocalTimeZone, today } from '@internationalized/date';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import { createInMemoryOnboardingService } from '../../../../core/users/services/inmemory-onboarding-service';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { GenerateOnboardingTokenDialogContainer } from './generate-onboarding-invitation-link-dialog.component';

const mockCopy = jest.fn();

jest.mock('../../../../hooks/use-clipboard/use-clipboard.hook', () => ({
    useClipboard: jest.fn(() => ({ copy: mockCopy })),
}));

describe('GenerateOnboardingTokenDialog', () => {
    let originalLocation: typeof window.location;

    beforeAll(() => {
        originalLocation = window.location;
        Object.defineProperty(window, 'location', {
            value: { origin: 'https://localhost' },
            writable: true,
        });
    });

    afterAll(() => {
        window.location = originalLocation;
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('should generate token and allow user to copy it', async () => {
        const originUrl = 'https://localhost';
        const token = 'cool-token';
        const link = `${originUrl}?signup-token=${token}`;

        const onboardingService = createInMemoryOnboardingService();
        onboardingService.generateToken = jest.fn(() => Promise.resolve({ onboardingToken: token }));

        render(<GenerateOnboardingTokenDialogContainer />, { services: { onboardingService } });

        fireEvent.click(screen.getByRole('button', { name: 'Create invitation link' }));

        expect(screen.getByRole('heading', { name: 'Create invitation link' })).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

        expect(await screen.findByRole('heading', { name: 'Copy invitation link' })).toBeVisible();
        expect(screen.getByText(link)).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: /Copy/ }));

        expect(mockCopy).toHaveBeenCalledWith(link, 'Onboarding invitation link copied successfully');
    });

    it('should generate tok with default dates range equal to 30 days', async () => {
        const todayDate = today(getLocalTimeZone());
        const endDate = todayDate.add({ days: 30 }).toString();

        const onboardingService = createInMemoryOnboardingService();
        onboardingService.generateToken = jest.fn(() => Promise.resolve({ onboardingToken: 'token' }));

        render(<GenerateOnboardingTokenDialogContainer />, { services: { onboardingService } });

        fireEvent.click(screen.getByRole('button', { name: 'Create invitation link' }));

        expect(screen.getByRole('heading', { name: 'Create invitation link' })).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

        await waitFor(() => {
            expect(onboardingService.generateToken).toHaveBeenCalledWith({
                dateFrom: todayDate.toString(),
                dateTo: endDate.toString(),
            });
        });
    });

    it('should show error notification message when token generation fails', async () => {
        const errorMessage = 'Token generation failed';
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.generateToken = jest.fn(() => Promise.reject({ message: errorMessage }));

        render(<GenerateOnboardingTokenDialogContainer />, { services: { onboardingService } });

        fireEvent.click(screen.getByRole('button', { name: 'Create invitation link' }));

        expect(screen.getByRole('heading', { name: 'Create invitation link' })).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

        await waitFor(() => {
            expect(onboardingService.generateToken).toHaveBeenCalled();
        });

        expect(screen.getByText(errorMessage)).toBeVisible();
    });
});
