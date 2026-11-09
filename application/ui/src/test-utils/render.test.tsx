// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useLocation, useNavigate } from 'react-router';

import { render } from './render';

const RerenderProbe = ({ label }: { label: string }) => {
    const [count, setCount] = useState(0);
    const queryClient = useQueryClient();
    const location = useLocation();
    const navigate = useNavigate();

    return (
        <>
            <p>{label}</p>
            <button
                onClick={() => {
                    setCount((value) => value + 1);
                    queryClient.setQueryData(['rerender-test'], 'cached');
                    void navigate('?updated=true');
                }}
            >
                Count {count}
            </button>
            <output aria-label='Current location'>{location.pathname + location.search}</output>
            <output aria-label='Cached value'>
                {queryClient.getQueryData<string>(['rerender-test']) ?? 'missing'}
            </output>
        </>
    );
};

describe('render', () => {
    it('updates props without resetting component state, router location or query cache', async () => {
        const user = userEvent.setup();
        const { rerender } = render(<RerenderProbe label='Before' />, { route: '/test', path: '/test' });

        await user.click(screen.getByRole('button', { name: 'Count 0' }));
        expect(screen.getByLabelText('Current location')).toHaveTextContent('/test?updated=true');

        rerender(<RerenderProbe label='After' />);

        expect(screen.getByText('After')).toBeVisible();
        expect(screen.queryByText('Before')).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Count 1' })).toBeVisible();
        expect(screen.getByLabelText('Current location')).toHaveTextContent('/test?updated=true');
        expect(screen.getByLabelText('Cached value')).toHaveTextContent('cached');
    });
});
