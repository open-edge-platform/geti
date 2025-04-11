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

import { render, screen } from '@testing-library/react';

import { AccuracyContainer } from './accuracy-container.component';

describe('Accuracy container', () => {
    it('should show "N/A" if value is null', () => {
        render(<AccuracyContainer value={null} heading='Accuracy' />);

        expect(screen.getByText('Accuracy is not available')).toBeInTheDocument();
    });

    it('should show score value properly rounded', () => {
        render(<AccuracyContainer value={0.76} heading='Accuracy' />);

        expect(screen.getByLabelText(/accuracy value/i)).toHaveTextContent('76%');
    });
});
