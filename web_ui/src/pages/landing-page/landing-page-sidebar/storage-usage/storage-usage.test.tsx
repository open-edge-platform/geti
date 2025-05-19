// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMediaQuery } from '@geti/ui';
import { render, screen } from '@testing-library/react';

import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import { checkTooltip } from '../../../../test-utils/utils';
import { ThemeProvider } from '../../../../theme/theme-provider.component';
import { StorageUsage } from './storage-usage.component';

jest.mock('../../../../core/status/hooks/use-status.hook', () => ({
    ...jest.requireActual('../../../../core/status/hooks/use-status.hook'),
    useStatus: jest.fn(),
}));

jest.mock('@react-spectrum/utils', () => ({
    ...jest.requireActual('@react-spectrum/utils'),
    useMediaQuery: jest.fn(() => true),
}));

describe('Storage usage', () => {
    const hitLimit = { data: { freeSpace: 20000000000, totalSpace: 100000000000, runningJobs: 0 } };
    const notHitLimit = { data: { freeSpace: 30000000000, totalSpace: 100000000000, runningJobs: 0 } };

    const renderApp = () => {
        return render(
            <ThemeProvider>
                <StorageUsage />
            </ThemeProvider>
        );
    };

    it('Should not display storage usage when limit (20 GB) is not exceeded', () => {
        // @ts-expect-error we only care about mocking data
        jest.mocked(useStatus).mockReturnValue(notHitLimit);

        renderApp();

        expect(screen.queryByLabelText('Storage usage')).not.toBeInTheDocument();
    });

    it('Should display storage usage when limit (20 GB) is hit', () => {
        // @ts-expect-error we only care about mocking data
        jest.mocked(useStatus).mockReturnValue(hitLimit);

        renderApp();

        expect(screen.getByLabelText('Storage usage')).toBeInTheDocument();
    });

    it('Should display percentage of storage usage', () => {
        // @ts-expect-error we only care about mocking data
        jest.mocked(useStatus).mockReturnValue(hitLimit);

        renderApp();

        const { freeSpace, totalSpace } = hitLimit.data;
        const DISK_USAGE = totalSpace - freeSpace;
        const DISK_USAGE_PERCENTAGE = (DISK_USAGE / totalSpace) * 100;

        expect(screen.getByText(`80 GB used of 100 GB`)).toBeInTheDocument();
        expect(screen.getByText(`${DISK_USAGE_PERCENTAGE}%`)).toBeInTheDocument();
    });

    it('Should display percentage of usage with tooltip but without description on small viewport', async () => {
        // @ts-expect-error we only care about mocking data
        jest.mocked(useStatus).mockReturnValue(hitLimit);
        jest.mocked(useMediaQuery).mockReturnValue(false);

        renderApp();

        const { freeSpace, totalSpace } = hitLimit.data;
        const DISK_USAGE = totalSpace - freeSpace;
        const DISK_USAGE_PERCENTAGE = (DISK_USAGE / totalSpace) * 100;

        expect(screen.getByText(`${DISK_USAGE_PERCENTAGE}%`)).toBeInTheDocument();
        expect(screen.queryByText(`80 GB used of 100 GB`)).not.toBeInTheDocument();

        await checkTooltip(
            screen.getByText(`${DISK_USAGE_PERCENTAGE}%`),
            '80 GB used of 100 GB. When the free storage hits 15 GB, many operations such as upload media, annotation, import, etc. will not be usable. Please free up some space by removing unnecessary files.'
        );
    });

    describe('Megabyte', () => {
        const megabyteHitLimit = { data: { freeSpace: 20000000, totalSpace: 100000000, runningJobs: 0 } };
        it('Should display percentage of storage usage', () => {
            // @ts-expect-error we only care about mocking data
            jest.mocked(useStatus).mockReturnValue(megabyteHitLimit);
            jest.mocked(useMediaQuery).mockReturnValue(true);

            renderApp();

            const { freeSpace, totalSpace } = megabyteHitLimit.data;
            const DISK_USAGE = totalSpace - freeSpace;
            const DISK_USAGE_PERCENTAGE = (DISK_USAGE / totalSpace) * 100;

            expect(screen.getByText(`80 MB used of 100 MB`)).toBeInTheDocument();
            expect(screen.getByText(`${DISK_USAGE_PERCENTAGE}%`)).toBeInTheDocument();
        });
    });
});
