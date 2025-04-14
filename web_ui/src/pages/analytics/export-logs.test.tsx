// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
