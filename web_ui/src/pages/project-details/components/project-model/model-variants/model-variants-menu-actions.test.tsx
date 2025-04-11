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

import { fireEvent, screen } from '@testing-library/react';

import * as sharedUtils from '../../../../../shared/utils';
import { getDownloadNotificationMessage } from '../../../../../shared/utils';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { ModelVariantsMenuActions } from './model-variants-menu-actions.component';

describe('ModelVariantsMenuActions', () => {
    const renderApp = (testUrl: string) => {
        return render(<ModelVariantsMenuActions modelId='123' downloadUrl={testUrl} handleOpenRunTest={jest.fn()} />);
    };

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('formats download url', async () => {
        const downloadFile = jest.spyOn(sharedUtils, 'downloadFile');
        const testUrl = 'model-download-url';
        await renderApp(testUrl);

        fireEvent.click(screen.getByRole('button', { name: /download model/i }));

        expect(downloadFile).toHaveBeenCalledWith(`/api/${testUrl}`);
        expect(await screen.findByText(getDownloadNotificationMessage('model'))).toBeInTheDocument();
    });
});
