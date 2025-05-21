// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ThemeProvider } from '@geti/ui/theme';
import { fireEvent, render, screen } from '@testing-library/react';

import { TrainingModelInfo } from './training-model-info.component';

describe('TrainingModelInfo', () => {
    it('displays training date, model training time and job duration', () => {
        render(
            <ThemeProvider>
                <TrainingModelInfo
                    trainingMetadata={[
                        {
                            value: '2024-10-10T11:40:13.045000+00:00',
                            header: 'Training date',
                            key: 'Training date',
                            type: 'text',
                        },
                        {
                            header: 'Training duration',
                            type: 'text',
                            key: 'Training duration',
                            value: '00:04:22',
                        },
                        {
                            header: 'Training job duration',
                            type: 'text',
                            key: 'Training job duration',
                            value: '00:08:22',
                        },
                    ]}
                />
            </ThemeProvider>
        );

        expect(screen.getByText('Training date')).toBeInTheDocument();
        expect(screen.getByText('10 October 2024')).toBeInTheDocument();
        expect(screen.getByText('11:40:13 AM')).toBeInTheDocument();

        expect(screen.getByText('Model training time')).toBeInTheDocument();
        expect(screen.getByText('00:04:22')).toBeInTheDocument();

        expect(screen.getByText('Job duration')).toBeInTheDocument();
        expect(screen.getByText('00:08:22')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /information/i }));
        expect(
            screen.getByText(
                'The total time includes loading data, training the model, and evaluating its performance.'
            )
        ).toBeInTheDocument();
    });
});
