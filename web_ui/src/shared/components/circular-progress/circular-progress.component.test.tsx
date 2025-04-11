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

import { render, screen } from '@testing-library/react';

import { CircularProgress } from './circular-progress.component';

const renderApp = (percentage: number) => {
    return render(<CircularProgress percentage={percentage} />);
};

describe('CircularProgress', () => {
    it('negative number', () => {
        renderApp(-10);
        expect(screen.getByText('0%')).toBeVisible();
    });

    it('int number', () => {
        renderApp(10);
        expect(screen.getByText('10%')).toBeVisible();
    });

    it('multiple decimals', () => {
        renderApp(21.6666666);
        expect(screen.getByText('21%')).toBeVisible();
    });

    it('single decimal', () => {
        renderApp(20.0);
        expect(screen.getByText('20%')).toBeVisible();
    });

    it('render "0"', () => {
        renderApp(0.5);
        expect(screen.getByText('0%')).toBeVisible();
    });
});
