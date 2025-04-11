// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

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
        render(<Analytics />, { featureFlags: { IS_GRAFANA_ENABLED: true } });

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
