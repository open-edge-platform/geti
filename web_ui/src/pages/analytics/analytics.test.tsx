// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { Environment, GPUProvider } from '../../core/platform-utils/dto/utils.interface';
import { createInMemoryPlatformUtilsService } from '../../core/platform-utils/services/create-in-memory-platform-utils-service';
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
            return {
                productVersion: '1.6.0',
                grafanaEnabled: true,
                gpuProvider: GPUProvider.INTEL,
                buildVersion: '1.6.0.test.123123',
                isSmtpDefined: true,
                intelEmail: 'support@geti.com',
                environment: Environment.ON_PREM,
            };
        };

        render(<Analytics />, { services: { platformUtilsService } });

        expect(await screen.findByRole('button', { name: /go to analytics/i })).toBeInTheDocument();
    });

    it.each(ANALYTICS_ITEMS)('should show dialog with date range picker for exporting %o', async (itemProps) => {
        render(<Analytics />);

        const downloadAnalyticsDataBtn = screen.getByRole('button', {
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
            screen.getByRole('button', {
                name: `Download ${SERVER_ITEM.header.toLocaleLowerCase()}`,
            })
        ).toBeInTheDocument();
    });
});
