// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryApiMaintenanceService } from '../../../core/maintenance/services/in-memory-api-maintenance-service';
import { MaintenanceResponse } from '../../../core/maintenance/services/maintenance.interface';
import { ApplicationServicesContextProps } from '../../../core/services/application-services-provider.component';
import { GENERAL_SETTINGS_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { createInMemoryUserSettingsService } from '../../../core/user-settings/services/in-memory-user-settings-service';
import { getMockedMaintenanceInfo } from '../../../test-utils/mocked-items-factory/mocked-maintenance';
import { getMockedUserGlobalSettings } from '../../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { MaintenanceBanner } from './maintenance-banner.component';

jest.mock('../../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(() => true),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({ organizationId: 'organizationId' })),
}));

const mockMaintenanceService = createInMemoryApiMaintenanceService();
const mockUserSettingsService = createInMemoryUserSettingsService();

const {
    maintenance: {
        window: {
            // https://www.epochconverter.com/
            start: mockStartTimeTimestamp, // April 28, 03:56
            end: mockEndTimeTimestamp, // September 10, 14:14
        },
    },
} = getMockedMaintenanceInfo();

const renderAppWithMaintenanceBanner = async (services: Partial<ApplicationServicesContextProps>) => {
    const component = await render(<MaintenanceBanner />, {
        services,
        featureFlags: { FEATURE_FLAG_MAINTENANCE_BANNER: true },
    });

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));

    return component;
};

describe('MaintenanceBanner', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders nothing if "maintenance" the response has no data', async () => {
        mockMaintenanceService.getMaintenanceInfo = jest.fn((): Promise<MaintenanceResponse> => Promise.reject());

        await renderAppWithMaintenanceBanner({ maintenanceService: mockMaintenanceService });

        expect(screen.queryByText(/Scheduled maintenance/)).not.toBeInTheDocument();
    });

    it('renders nothing if "maintenance" is is not enabled', async () => {
        mockMaintenanceService.getMaintenanceInfo = jest.fn(
            (): Promise<MaintenanceResponse> =>
                Promise.resolve(
                    getMockedMaintenanceInfo({
                        maintenance: { enabled: false, window: { start: 0, end: 0 } },
                    })
                )
        );

        await renderAppWithMaintenanceBanner({ maintenanceService: mockMaintenanceService });

        expect(screen.queryByText(/Scheduled maintenance/)).not.toBeInTheDocument();
    });

    it('renders correct date information if "maintenance" is enabled - same day', async () => {
        const mockStartTimeTimestampSameDay = 1711312113376; // April 28, 03:56
        const mockStartTimeTimestampSameDayAfterOneHour = 1711312116976; // April 28, 04:56

        mockMaintenanceService.getMaintenanceInfo = jest.fn(
            (): Promise<MaintenanceResponse> =>
                Promise.resolve(
                    getMockedMaintenanceInfo({
                        maintenance: {
                            enabled: true,
                            window: {
                                start: mockStartTimeTimestampSameDay,
                                end: mockStartTimeTimestampSameDayAfterOneHour,
                            },
                        },
                    })
                )
        );

        await renderAppWithMaintenanceBanner({ maintenanceService: mockMaintenanceService });

        expect(screen.getByText(/Scheduled maintenance/)).toBeVisible();
        expect(screen.getAllByText(/28 of April/)).toHaveLength(1);
        expect(screen.getByText(/28 of April, 03:56/)).toBeVisible();
        expect(screen.getByText(/04:56 UTC/)).toBeVisible();
    });

    it('renders correct date information if "maintenance" is enabled - different days', async () => {
        const mockStartTimestampNovember7 = 1730985374; // Thursday, 7 November 2024 13:16:14
        const mockEndTimeTimestampNovember10 = 1731244574; // Sunday, 10 November 2024 13:16:14

        mockMaintenanceService.getMaintenanceInfo = jest.fn(
            (): Promise<MaintenanceResponse> =>
                Promise.resolve(
                    getMockedMaintenanceInfo({
                        maintenance: {
                            enabled: true,
                            window: {
                                start: mockStartTimestampNovember7,
                                end: mockEndTimeTimestampNovember10,
                            },
                        },
                    })
                )
        );

        await renderAppWithMaintenanceBanner({ maintenanceService: mockMaintenanceService });

        expect(screen.getByText(/Scheduled maintenance/)).toBeVisible();
        expect(screen.getByText(/7 of November, 13:16/)).toBeVisible();
        expect(screen.getByText(/10 of November, 13:16/)).toBeVisible();
    });

    it('updates settings when dismissed', async () => {
        mockMaintenanceService.getMaintenanceInfo = jest.fn(
            (): Promise<MaintenanceResponse> =>
                Promise.resolve(
                    getMockedMaintenanceInfo({
                        maintenance: {
                            enabled: true,
                            window: {
                                start: mockStartTimeTimestamp,
                                end: mockEndTimeTimestamp,
                            },
                        },
                    })
                )
        );

        const mockSaveSettings = jest.fn(async () => Promise.resolve());
        mockUserSettingsService.saveGlobalSettings = mockSaveSettings;

        await renderAppWithMaintenanceBanner({
            maintenanceService: mockMaintenanceService,
            userSettingsService: mockUserSettingsService,
        });

        expect(screen.getByText(/Scheduled maintenance/)).toBeVisible();

        fireEvent.click(screen.getByLabelText('dismiss banner'));

        await waitFor(() => {
            expect(mockSaveSettings).toHaveBeenCalledWith(
                expect.objectContaining({
                    [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: { wasDismissed: true, window: expect.anything() },
                })
            );
        });
    });

    it('does not render if it was previously dismissed for the specified epoch', async () => {
        mockMaintenanceService.getMaintenanceInfo = jest.fn(
            (): Promise<MaintenanceResponse> =>
                Promise.resolve(
                    getMockedMaintenanceInfo({
                        maintenance: {
                            enabled: true,
                            window: { start: mockStartTimeTimestamp, end: mockEndTimeTimestamp },
                        },
                    })
                )
        );

        mockUserSettingsService.getGlobalSettings = async () =>
            getMockedUserGlobalSettings({
                [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
                    wasDismissed: true,
                    window: { start: mockStartTimeTimestamp, end: mockEndTimeTimestamp },
                },
            });

        await renderAppWithMaintenanceBanner({
            maintenanceService: mockMaintenanceService,
            userSettingsService: mockUserSettingsService,
        });

        expect(screen.queryByText(/Scheduled maintenance/)).not.toBeInTheDocument();
    });

    it('renders if it was previously dismissed but for a different epoch', async () => {
        mockMaintenanceService.getMaintenanceInfo = jest.fn(
            (): Promise<MaintenanceResponse> =>
                Promise.resolve(
                    getMockedMaintenanceInfo({
                        maintenance: {
                            enabled: true,
                            window: {
                                start: mockStartTimeTimestamp,
                                end: mockEndTimeTimestamp,
                            },
                        },
                    })
                )
        );

        mockUserSettingsService.getGlobalSettings = () =>
            Promise.resolve(
                getMockedUserGlobalSettings({
                    [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
                        wasDismissed: true,
                        window: { start: mockStartTimeTimestamp - 1, end: mockEndTimeTimestamp },
                    },
                })
            );

        await renderAppWithMaintenanceBanner({
            maintenanceService: mockMaintenanceService,
            userSettingsService: mockUserSettingsService,
        });

        expect(screen.getByText(/Scheduled maintenance/)).toBeVisible();
        expect(screen.getByText(/28 of April, 03:56/)).toBeVisible();
        expect(screen.getByText(/10 of September, 14:14/)).toBeVisible();
    });
});
