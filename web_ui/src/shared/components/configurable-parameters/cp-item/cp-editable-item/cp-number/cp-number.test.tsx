// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider } from '@geti/ui';
import { fireEvent, render, screen } from '@testing-library/react';

import { CPNumber } from './cp-number.component';

describe('CPNumber', () => {
    it('Renders number and slider fields for a integer parameter', async () => {
        const updateParameter = jest.fn();
        const parameter = {
            description:
                'The minimum number of new annotations required before auto-train is triggered. Auto-training will start every time that this number of annotations is created.',
            editable: true,
            header: 'Number of images required for auto-training',
            name: 'required_images_auto_training',
            value: 8200,
            warning: null,
            id: '6718bc10e809d34060ea6df9::6718bc1066b74ae3aaefbebe::5558a488-cb47-4521-800d-44e341135a12',
            dataType: 'integer',
            templateType: 'input',
            defaultValue: 12,
            minValue: 3,
            maxValue: 10000,
        } as const;

        render(
            <Provider theme={defaultTheme}>
                <CPNumber
                    id={'number-of-images-required-for-auto-training'}
                    parameter={parameter}
                    updateParameter={updateParameter}
                />
            </Provider>
        );

        const numberField = screen.getByRole('textbox');
        expect(numberField).toHaveValue('8,200');

        fireEvent.change(numberField, { target: { value: 5000 } });
        fireEvent.focusOut(numberField);
        expect(updateParameter).toHaveBeenCalledWith(parameter.id, 5000);

        const slider = screen.getByRole('slider');
        expect(slider).toHaveValue(`${parameter.value}`);

        fireEvent.change(slider, { target: { value: 6000 } });
        expect(updateParameter).toHaveBeenCalledWith(parameter.id, 6000);
    });

    it('Renders number and slider fields for a float parameter', async () => {
        const updateParameter = jest.fn();
        const parameter = {
            description: 'Fraction of annotated data that will be assigned to the training set',
            editable: true,
            header: 'Training set proportion',
            name: 'train_proportion',
            step_size: null,
            ui_rules: {
                action: 'SHOW',
                operator: 'AND',
                rules: [
                    {
                        operator: 'EQUAL_TO',
                        parameter: ['auto_subset_fractions'],
                        type: 'RULE',
                        value: false,
                    },
                ],
                type: 'UI_RULES',
            },
            value: 0.5,
            warning: 'When the proportions do not add up to 1, they will be rescaled to add up to 1.',
            id: '6718bc10e809d34060ea6df9::6718bc1066b74ae3aaefbebd::d8648aea-6fbd-4eba-8b81-b6215a2b77c1::18e3a4a9-bc50-4527-9d5f-2a949ef26b4f',
            dataType: 'float',
            templateType: 'input',
            defaultValue: 0.5,
            minValue: 0.1,
            maxValue: 1,
        } as const;

        render(
            <Provider theme={defaultTheme}>
                <CPNumber
                    id={'number-of-images-required-for-autotraining-set-proportiontraining'}
                    parameter={parameter}
                    updateParameter={updateParameter}
                />
            </Provider>
        );

        const numberField = screen.getByRole('textbox');
        expect(numberField).toHaveValue('0.5');

        fireEvent.change(numberField, { target: { value: 0.4 } });
        fireEvent.focusOut(numberField);
        expect(updateParameter).toHaveBeenCalledWith(parameter.id, 0.4);

        const slider = screen.getByRole('slider');
        expect(slider).toHaveValue(`${parameter.value}`);

        fireEvent.change(slider, { target: { value: 0.6 } });
        expect(updateParameter).toHaveBeenCalledWith(parameter.id, 0.6);
    });
});
