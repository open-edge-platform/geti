// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { TrainingConfiguration } from '@/api/types';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from 'test-utils/render';

import { Training } from './training.component';

it('updates the validation metric in evaluation settings', async () => {
    const initial: TrainingConfiguration = {
        parameters: [
            {
                type: 'parameter_group',
                key: 'evaluation',
                name: 'Evaluation parameters',
                description: 'Evaluation settings',
                depends_on: null,
                parameters: [
                    {
                        type: 'parameter',
                        key: 'validation_metric',
                        name: 'Validation metric',
                        description: 'Validation metric',
                        value_type: 'str',
                        value: 'default',
                        default_value: 'default',
                        allowed_values: ['default', 'map', 'map_50'],
                        depends_on: null,
                    },
                ],
            },
        ],
    };
    const App = () => {
        const [configuration, setConfiguration] = useState<TrainingConfiguration | undefined>(initial);
        return (
            <>
                <Training
                    trainingConfiguration={configuration ?? initial}
                    defaultTrainingConfiguration={initial}
                    onTrainingConfigurationChange={setConfiguration}
                />
                <output>{JSON.stringify(configuration)}</output>
            </>
        );
    };
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Select Validation metric/ }));
    await userEvent.click(screen.getByRole('option', { name: 'map_50' }));
    expect(screen.getByRole('status')).toHaveTextContent('"value":"map_50"');
});
