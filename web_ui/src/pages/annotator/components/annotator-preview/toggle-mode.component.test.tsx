// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { checkTooltip } from '../../../../test-utils/utils';
import { ANNOTATOR_MODE } from '../../core/annotation-tool-context.interface';
import { annotatorRender } from '../../test-utils/annotator-render';
import { ToggleMode } from './toggle-mode.component';

describe('ToggleMode', () => {
    const renderApp = (setMode = jest.fn()) => {
        return annotatorRender(<ToggleMode mode={ANNOTATOR_MODE.ACTIVE_LEARNING} setMode={setMode} />);
    };

    it('annotation mode', async () => {
        const setMode = jest.fn();
        await renderApp(setMode);

        const button = screen.getByRole('button', { name: /select annotation mode/i });
        await checkTooltip(button, 'User annotation mode');

        fireEvent.click(button);

        expect(setMode).toHaveBeenCalledWith(ANNOTATOR_MODE.ACTIVE_LEARNING);
    });

    it('predictions mode', async () => {
        const setMode = jest.fn();
        await renderApp(setMode);

        const button = screen.getByRole('button', { name: /select prediction mode/i });

        await checkTooltip(button, 'AI prediction mode');

        fireEvent.click(button);
        expect(setMode).toHaveBeenCalledWith(ANNOTATOR_MODE.PREDICTION);
    });
});
