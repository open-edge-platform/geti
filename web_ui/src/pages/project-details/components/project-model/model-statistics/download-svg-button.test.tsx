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

import { useRef } from 'react';

import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import {
    downloadMultiplePages,
    ERROR_MESSAGE,
} from '../../../../../shared/components/download-graph-menu/export-svg-utils';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { DownloadSvgButton } from './download-svg-button.component';

jest.mock('../../../../../shared/components/download-graph-menu/export-svg-utils', () => ({
    ...jest.requireActual('../../../../../shared/components/download-graph-menu/export-svg-utils'),
    downloadMultiplePages: jest.fn(() => Promise.resolve()),
}));

describe('DownloadSvgButton', () => {
    const RenderApp = () => {
        const container = useRef(null);
        return (
            <>
                <div ref={container}></div>

                <DownloadSvgButton
                    fileName={'file-name'}
                    marginEnd={'size-100'}
                    tooltip={'Download graph'}
                    graphBackgroundColor={'gray-100'}
                    container={container}
                />
            </>
        );
    };
    it('shows the download button', async () => {
        await render(<RenderApp />);

        expect(screen.getByRole('button', { name: 'download svg' })).toBeVisible();
    });

    it('shows error warning', async () => {
        jest.mocked(downloadMultiplePages).mockRejectedValue('');
        await render(<RenderApp />);

        await userEvent.click(screen.getByRole('button', { name: 'download svg' }));

        await waitFor(() => {
            expect(screen.queryByText(ERROR_MESSAGE)).toBeVisible();
            expect(screen.getByRole('button', { name: 'download svg' })).toBeEnabled();
        });
    });
});
