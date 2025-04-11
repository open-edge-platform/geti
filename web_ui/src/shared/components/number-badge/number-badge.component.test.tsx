// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen } from '@testing-library/react';

import { NumberBadge } from './number-badge.component';

describe('NumberBadge', () => {
    it('should show a loading UI if the jobsNumber is "null"', () => {
        render(<NumberBadge id='fake-id' jobsNumber={null} />);

        expect(screen.getByLabelText('Loading...')).toBeInTheDocument();
    });

    it('should show a loading UI if "isPending" is true', () => {
        render(<NumberBadge id='fake-id' jobsNumber={3} isPending />);

        expect(screen.getByLabelText('Loading...')).toBeInTheDocument();
    });

    it('should not render anything if jobsNumber is 0', () => {
        render(<NumberBadge id='fake-id' jobsNumber={0} />);

        expect(screen.queryByTestId('number badge')).not.toBeInTheDocument();
    });

    it('should render properly with a valid number', () => {
        render(<NumberBadge id='fake-id' jobsNumber={3} />);

        expect(screen.getByTestId('number badge')).toBeInTheDocument();
        expect(screen.getByTestId('number-badge-fake-id-value')).toBeInTheDocument();
        expect(screen.getByTestId('number-badge-fake-id-value')).toHaveTextContent('3');
    });
});
