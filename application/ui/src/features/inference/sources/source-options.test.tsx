// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse } from 'msw';
import { render } from 'test-utils/render';

import { http } from '../../../api/utils';
import { server } from '../../../msw-node-setup';
import { SourceOptions } from './source-options';

describe('SourceOptions', () => {
    beforeEach(() => {
        server.use(http.get('/api/system/devices/camera', () => HttpResponse.json([])));
    });

    const renderOptions = () =>
        render(
            <SourceOptions existingNames={[]} onSaved={rs.fn()} hasHeader={false}>
                <span>header</span>
            </SourceOptions>
        );

    it('shows the header only when hasHeader is set', () => {
        render(
            <SourceOptions existingNames={[]} onSaved={rs.fn()} hasHeader>
                <span>header</span>
            </SourceOptions>
        );

        expect(screen.getByText('header')).toBeInTheDocument();
    });

    it.each([
        ['USB Camera', () => screen.findByRole('button', { name: /Camera list/i })],
        ['IP Camera', () => screen.findByRole('textbox', { name: /Stream Url/i })],
        ['Video file', () => screen.findByTestId('upload-video-file')],
    ])('expanding "%s" shows its fields', async (label, findField) => {
        renderOptions();

        await userEvent.click(screen.getByRole('button', { name: label }));

        expect(await findField()).toBeInTheDocument();
    });
});
