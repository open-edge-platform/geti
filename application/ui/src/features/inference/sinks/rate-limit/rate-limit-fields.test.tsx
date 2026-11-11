// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from 'test-utils/render';

import { RateLimitFields } from './rate-limit-fields.component';

describe('RateLimitFields', () => {
    it('shows empty fields when value is null', () => {
        render(<RateLimitFields value={null} onChange={rs.fn()} />);

        expect(screen.getByRole('textbox', { name: /samples/i })).toHaveValue('');
        expect(screen.getByRole('textbox', { name: /seconds/i })).toHaveValue('');
    });

    it('shows initial value as samples per 1 second', () => {
        render(<RateLimitFields value={0.5} onChange={rs.fn()} />);

        expect(screen.getByRole('textbox', { name: /samples/i })).toHaveValue('0.5');
        expect(screen.getByRole('textbox', { name: /seconds/i })).toHaveValue('1');
    });

    it('emits null while only one of the fields is filled', async () => {
        const onChange = rs.fn();
        render(<RateLimitFields value={null} onChange={onChange} />);

        await userEvent.type(screen.getByRole('textbox', { name: /samples/i }), '3');
        await userEvent.tab();

        expect(onChange).toHaveBeenLastCalledWith(null);
    });

    it('emits the rate (samples per second) once both fields are filled', async () => {
        const onChange = rs.fn();
        render(<RateLimitFields value={null} onChange={onChange} />);

        await userEvent.type(screen.getByRole('textbox', { name: /samples/i }), '3');
        await userEvent.type(screen.getByRole('textbox', { name: /seconds/i }), '2');
        await userEvent.tab();

        expect(onChange).toHaveBeenLastCalledWith(1.5);
    });

    it('emits null when samples are cleared', async () => {
        const onChange = rs.fn();
        render(<RateLimitFields value={5} onChange={onChange} />);

        await userEvent.clear(screen.getByRole('textbox', { name: /samples/i }));
        await userEvent.tab();

        expect(onChange).toHaveBeenLastCalledWith(null);
    });
});
