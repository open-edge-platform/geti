// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as sharedUtils from '@shared/utils';
import { getDownloadNotificationMessage } from '@shared/utils';
import { fireEvent, screen } from '@testing-library/react';

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
