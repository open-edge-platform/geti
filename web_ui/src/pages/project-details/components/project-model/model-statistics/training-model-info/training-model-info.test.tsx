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

import { fireEvent, render, screen } from '@testing-library/react';

import { ThemeProvider } from '../../../../../../theme/theme-provider.component';
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
