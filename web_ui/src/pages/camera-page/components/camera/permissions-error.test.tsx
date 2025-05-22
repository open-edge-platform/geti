// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider } from '@geti/ui';
import { screen, waitFor } from '@testing-library/react';

import { providersRender } from '../../../../test-utils/required-providers-render';
import { PermissionError } from './permissions-error.component';

describe('PermissionError', () => {
    const renderApp = () => {
        providersRender(
            <Provider theme={defaultTheme}>
                <PermissionError />
            </Provider>
        );
    };

    it('render notification toast', async () => {
        renderApp();

        await waitFor(() => {
            expect(screen.getByLabelText('notification toast')).toBeVisible();
            expect(screen.getAllByText('Camera connection is lost')).toHaveLength(2);
            expect(screen.getAllByText('Please check your device and network settings and try again.')).toHaveLength(2);
        });
    });
});
