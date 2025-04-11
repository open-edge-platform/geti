// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';

// other than those that are expressly stated in the License.
export const selectClassificationDomain = () => {
    fireEvent.click(screen.getByRole('tab', { name: 'Classification' }));
};

export const selectAnomalyDomain = () => {
    fireEvent.click(screen.getByRole('tab', { name: 'Anomaly' }));
};

export const clickNextButton = () => {
    const nextButtonTemplate = screen.getByRole('button', { name: 'Next' });

    expect(nextButtonTemplate).toBeEnabled();
    fireEvent.click(nextButtonTemplate);
};

export const clickBackButton = () => {
    const previousButtonTemplate = screen.getByRole('button', { name: 'Back' });

    expect(previousButtonTemplate).toBeEnabled();
    fireEvent.click(previousButtonTemplate);
};

export const typeIntoTextbox = async (name: string, textBoxName: string) => {
    const textField = await screen.findByRole('textbox', { name: textBoxName });

    fireEvent.change(textField, { target: { value: name } });
};

export const clearTextBox = (textBoxName: string) => {
    fireEvent.change(screen.getByRole('textbox', { name: textBoxName }), { target: { value: '' } });
};

export const selectDetectionClassificationChain = () => {
    const tab = screen.getByRole('tab', { name: 'Chained tasks' });
    fireEvent.click(tab);

    const detectionClassificationChain = screen.getByTestId('Detection-Classification');
    fireEvent.click(detectionClassificationChain);
};

export const selectDetectionSegmentationChain = () => {
    const tab = screen.getByRole('tab', { name: 'Chained tasks' });
    fireEvent.click(tab);

    const detectionSegmentationChain = screen.getByTestId('Detection-Segmentation');
    fireEvent.click(detectionSegmentationChain);
};
