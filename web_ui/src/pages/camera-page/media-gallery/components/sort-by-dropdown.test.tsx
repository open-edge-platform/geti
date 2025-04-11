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
import { fireEvent, render, screen } from '@testing-library/react';

import { SortingOptions } from '../../util';
import { SortByDropdown } from './sort-by-dropdown.component';

describe('SortByDropdown', () => {
    it('"Most Recent" is selected by default', async () => {
        const mockedOnSelect = jest.fn();

        await render(
            <Provider theme={defaultTheme}>
                <SortByDropdown onSelect={mockedOnSelect} />
            </Provider>
        );

        expect(screen.getByRole('button', { name: 'Most Recent sorting options' })).toBeVisible();
        fireEvent.click(screen.getByRole('button', { name: 'Most Recent sorting options' }));
        fireEvent.click(screen.getByRole('option', { name: 'Label Name (A-Z)' }));

        expect(mockedOnSelect).toHaveBeenCalledWith(SortingOptions.LABEL_NAME_A_Z);
    });
});
