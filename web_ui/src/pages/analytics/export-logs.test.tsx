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

import { ComponentProps } from 'react';

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../test-utils/required-providers-render';
import { ExportAnalyticsData, ExportAnalyticsSubTypes, ExportAnalyticsType } from './export-logs.component';

describe('ExportLogs', () => {
    const mockedUrls = [() => 'urls'];
    const ANALYTICS_WITH_SUBTYPES = [ExportAnalyticsType.METRICS, ExportAnalyticsType.LOGS];

    const selectSubtype = (subtype: ExportAnalyticsSubTypes, type: ExportAnalyticsType) => {
        fireEvent.click(screen.getByRole('radio', { name: `${subtype} ${type.toLocaleLowerCase()}` }));
    };

    const renderExportLogs = async (exportType: ComponentProps<typeof ExportAnalyticsData>['exportType']) => {
        render(<ExportAnalyticsData exportType={exportType} urls={mockedUrls} />);

        fireEvent.click(screen.getByRole('button', { name: /Download/ }));
    };

    it('Should not display subtype radio buttons and button should be enabled for traces', async () => {
        await renderExportLogs(ExportAnalyticsType.TRACES);

        expect(screen.queryByLabelText('Traces type')).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Export' })).toBeEnabled();
    });

    it.each(ANALYTICS_WITH_SUBTYPES)(
        'Should display subtype radio buttons and button should be disabled for %o',
        async (type) => {
            await renderExportLogs(type);

            expect(screen.getByLabelText(`${type} type`)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'Export' })).toBeDisabled();
        }
    );

    it.each(ANALYTICS_WITH_SUBTYPES)(
        'Should export button be enabled once subtype for %o is selected',
        async (type) => {
            await renderExportLogs(type);

            selectSubtype(ExportAnalyticsSubTypes.APPLICATION, type);

            expect(screen.getByRole('button', { name: 'Export' })).toBeEnabled();

            selectSubtype(ExportAnalyticsSubTypes.SERVER, type);

            expect(screen.getByRole('button', { name: 'Export' })).toBeEnabled();
        }
    );
});
