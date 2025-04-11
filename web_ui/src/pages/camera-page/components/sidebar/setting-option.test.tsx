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

import { defaultTheme, Provider as ThemeProvider } from '@adobe/react-spectrum';
import { fireEvent } from '@testing-library/dom';
import { render, screen } from '@testing-library/react';

import { SettingMinMax, SettingSelection } from '../../providers/util';
import { SettingOption, SettingOptionProps } from './setting-option.component';

const mockedMinMaxConfig: SettingMinMax = {
    min: 1,
    max: 200,
    value: 100,
    type: 'minMax',
};

const mockedSelectionConfig: SettingSelection = {
    type: 'selection',
    value: 'none',
    options: ['none', 'crop-and-scale'],
};

describe('SettingOption', () => {
    const renderApp = (props: SettingOptionProps) => {
        render(
            <ThemeProvider theme={defaultTheme}>
                <SettingOption {...props} />
            </ThemeProvider>
        );
    };

    it('resets initial value', () => {
        const mockedOnChange = jest.fn();
        const label = 'label-name-test';
        renderApp({ onChange: mockedOnChange, label, config: mockedMinMaxConfig });

        fireEvent.keyDown(screen.getByRole('slider'), { key: 'Right' });

        expect(mockedOnChange).toHaveBeenNthCalledWith(1, '101');

        fireEvent.click(screen.getByRole('button', { name: `reset ${label}` }));
        expect(mockedOnChange).toHaveBeenNthCalledWith(2, `${mockedMinMaxConfig.value}`);
    });

    it('render selection options', () => {
        const mockedOnChange = jest.fn();
        const label = 'label-name-test';
        renderApp({ onChange: mockedOnChange, label, config: mockedSelectionConfig });

        expect(screen.getByLabelText(`${label} selection options`)).toBeVisible();
    });
});
