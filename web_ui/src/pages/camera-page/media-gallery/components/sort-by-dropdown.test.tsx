// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
