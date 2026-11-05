// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from 'test-utils/render';

import { SinkOptions } from './sink-options';

describe('SinkOptions', () => {
    const renderOptions = (hasHeader = false) =>
        render(
            <SinkOptions onSaved={rs.fn()} hasHeader={hasHeader}>
                <span>header</span>
            </SinkOptions>
        );

    it('shows the header only when hasHeader is set', () => {
        const { unmount } = renderOptions(false);
        expect(screen.queryByText('header')).not.toBeInTheDocument();
        unmount();

        renderOptions(true);
        expect(screen.getByText('header')).toBeInTheDocument();
    });

    it.each([
        ['Folder', /Folder Path/i],
        ['Webhook', /Webhook URL/i],
        ['MQTT', /Broker Host/i],
    ])('expanding "%s" shows its fields', async (label, name) => {
        renderOptions();

        await userEvent.click(screen.getByRole('button', { name: label }));

        expect(await screen.findByRole('textbox', { name })).toBeInTheDocument();
    });
});
