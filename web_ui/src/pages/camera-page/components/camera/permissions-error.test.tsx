// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { defaultTheme, Provider } from '@adobe/react-spectrum';
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
