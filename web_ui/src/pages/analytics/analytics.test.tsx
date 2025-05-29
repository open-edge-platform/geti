// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { createInMemoryPlatformUtilsService } from '../../core/platform-utils/services/create-in-memory-platform-utils-service';
import { getMockedProductInfo } from '../../test-utils/mocked-items-factory/mocked-product-info';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { Analytics } from './analytics.component';
import { ExportServerType } from './downloadable-item.component';
import { ExportAnalyticsType } from './export-logs.component';

describe('Analytics', () => {
    const ANALYTICS_ITEMS = [
        { header: ExportAnalyticsType.METRICS },
        { header: ExportAnalyticsType.TRACES },
        { header: ExportAnalyticsType.LOGS },
    ];
    const SERVER_ITEM = { header: ExportServerType.SERVER_INFO };

    it('should display card for external analytics dashboard', async () => {
        const platformUtilsService = createInMemoryPlatformUtilsService();
        platformUtilsService.getProductInfo = async () => {
            return getMockedProductInfo({
                grafanaEnabled: true,
            });
        };

        render(<Analytics />, { services: { platformUtilsService } });

        expect(await screen.findByRole('button', { name: /go to analytics/i })).toBeInTheDocument();
    });

    it.each(ANALYTICS_ITEMS)('should show dialog with date range picker for exporting %o', async (itemProps) => {
        render(<Analytics />);

        const downloadAnalyticsDataBtn = await screen.findByRole('button', {
            name: `Download ${itemProps.header.toLocaleLowerCase()}`,
        });

        expect(downloadAnalyticsDataBtn).toBeInTheDocument();

        fireEvent.click(downloadAnalyticsDataBtn);

        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(
            screen.getByRole('button', {
                name: /calendar dates range/i,
            })
        ).toBeInTheDocument();
    });

    it('Server info should have a download button', async () => {
        render(<Analytics />);

        expect(
            await screen.findByRole('button', {
                name: `Download ${SERVER_ITEM.header.toLocaleLowerCase()}`,
            })
        ).toBeInTheDocument();
    });
});
