// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
