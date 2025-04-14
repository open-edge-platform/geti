// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { FullscreenAction } from './fullscreen-action.component';

describe('Fullscreen action', () => {
    it('Check if action opens and closes fullscreen', async () => {
        render(
            <FullscreenAction title={'Test fullscreen'}>
                <div data-testid={'test-fullscreen'} />
            </FullscreenAction>
        );

        expect(screen.queryByTestId('test-fullscreen')).not.toBeInTheDocument();
        const expandButton = screen.getByRole('button', { name: /Open in fullscreen/ });
        fireEvent.click(expandButton);

        const dialog = screen.queryByRole('dialog');
        expect(dialog).toBeInTheDocument();

        expect(screen.getByText('Test fullscreen')).toBeInTheDocument();
        expect(screen.getByTestId('test-fullscreen')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Close fullscreen' }));
        expect(dialog).not.toBeInTheDocument();
    });
});
