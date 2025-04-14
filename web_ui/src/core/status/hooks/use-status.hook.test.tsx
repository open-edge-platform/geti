// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';

import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { CustomFeatureFlags } from '../../feature-flags/services/feature-flag-service.interface';
import { createInMemoryStatusService } from '../services/in-memory-status-service';
import { useStatus } from './use-status.hook';
import {
    LOW_FREE_DISK_SPACE_IN_BYTES,
    LOW_FREE_DISK_SPACE_MESSAGE,
    TOO_LOW_FREE_DISK_SPACE_IN_BYTES,
    TOO_LOW_FREE_DISK_SPACE_MESSAGE,
} from './utils';

const mockedGetStatus = jest.fn();

const mockAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

jest.mock('../../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(() => false),
}));

const renderStatusHook = (params: { featureFlags?: CustomFeatureFlags; children?: ReactNode } = {}) => {
    const statusService = createInMemoryStatusService();
    statusService.getStatus = mockedGetStatus;

    return renderHookWithProviders(useStatus, {
        providerProps: { featureFlags: params.featureFlags, statusService },
    });
};

describe('useStatus', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('shows a warning when free space is less than low threshold and greater than too low threshold', async () => {
        mockedGetStatus.mockImplementationOnce(() => Promise.resolve({ freeSpace: LOW_FREE_DISK_SPACE_IN_BYTES - 1 }));

        renderStatusHook();

        await waitFor(() => {
            expect(mockAddNotification).toHaveBeenCalledWith({
                message: LOW_FREE_DISK_SPACE_MESSAGE,
                type: NOTIFICATION_TYPE.WARNING,
                dismiss: { duration: 0 },
            });
        });
    });

    it('shows an error when free space is less than too low threshold', async () => {
        mockedGetStatus.mockImplementationOnce(() =>
            Promise.resolve({ freeSpace: TOO_LOW_FREE_DISK_SPACE_IN_BYTES - 1 })
        );
        renderStatusHook();

        await waitFor(() => {
            expect(mockAddNotification).toHaveBeenCalledWith({
                message: TOO_LOW_FREE_DISK_SPACE_MESSAGE,
                type: NOTIFICATION_TYPE.ERROR,
                dismiss: { duration: 0 },
            });
        });
    });

    describe('does not show the notification', () => {
        it('freeSpace is greater than low threshold', async () => {
            mockedGetStatus.mockImplementationOnce(() =>
                Promise.resolve({ freeSpace: `${LOW_FREE_DISK_SPACE_IN_BYTES + 1}` })
            );
            const { result } = renderStatusHook();

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.data).toBeDefined();
            });

            expect(mockAddNotification).not.toHaveBeenCalled();
        });

        it('with feature flag off', async () => {
            mockedGetStatus.mockImplementationOnce(() =>
                Promise.resolve({ freeSpace: `${LOW_FREE_DISK_SPACE_IN_BYTES + 1}` })
            );

            const { result } = renderStatusHook({
                children: <></>,
                featureFlags: { FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: false },
            });

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.data).toBeDefined();
            });

            expect(mockAddNotification).not.toHaveBeenCalled();
        });

        it('on a saas environment', async () => {
            mockedGetStatus.mockImplementationOnce(() =>
                Promise.resolve({ freeSpace: `${LOW_FREE_DISK_SPACE_IN_BYTES + 1}` })
            );
            jest.mocked(useIsSaasEnv).mockImplementation(() => true);

            const { result } = renderStatusHook({
                children: <></>,
            });

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.data).toBeDefined();
            });

            expect(mockAddNotification).not.toHaveBeenCalled();
        });
    });
});
