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
