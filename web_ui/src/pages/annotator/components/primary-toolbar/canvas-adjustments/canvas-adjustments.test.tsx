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
import { userEvent } from '@testing-library/user-event';

import { getMockedUserProjectSettingsObject } from '../../../../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { AnnotatorCanvasSettingsProvider } from '../../../providers/annotator-canvas-settings-provider/annotator-canvas-settings-provider.component';
import { CanvasAdjustments } from './canvas-adjustments.component';

jest.mock('../../../providers/annotator-provider/annotator-provider.component', () => ({
    ...jest.requireActual('../../../providers/annotator-provider/annotator-provider.component'),
    useAnnotator: jest.fn(() => ({
        canvasSettings: {
            canvasSettingsState: [{}, jest.fn()],
            handleSaveConfig: jest.fn(),
        },
    })),
}));

describe('CanvasAdjustments', () => {
    const saveConfig = jest.fn();
    const defaultSettings = getMockedUserProjectSettingsObject({ saveConfig });

    const renderCanvasAdjustments = async () => {
        render(
            <AnnotatorCanvasSettingsProvider settings={defaultSettings}>
                <CanvasAdjustments />
            </AnnotatorCanvasSettingsProvider>
        );

        await userEvent.click(screen.getByRole('button', { name: /Canvas adjustments/i }));
    };

    it('Canvas settings should be not be saved on close event when settings are the same', async () => {
        await renderCanvasAdjustments();

        await userEvent.click(screen.getByRole('button', { name: /Close canvas adjustments/i }));

        expect(saveConfig).not.toHaveBeenCalled();
    });

    it('Canvas settings should be save on close event', async () => {
        await renderCanvasAdjustments();

        fireEvent.change(screen.getByRole('slider', { name: /label opacity adjustment/i }), { target: { value: 0.5 } });

        await userEvent.click(screen.getByRole('button', { name: /Close canvas adjustments/i }));

        expect(saveConfig).toHaveBeenCalled();
    });

    it('Enabling "Hide labels" should disable labels opacity', async () => {
        await renderCanvasAdjustments();

        const hideLabels = screen.getByRole('switch', { name: 'Hide labels' });

        await userEvent.click(hideLabels);

        expect(hideLabels).toBeEnabled();
        expect(screen.getByRole('slider', { name: /label opacity adjustment/i })).toBeDisabled();
    });
});
