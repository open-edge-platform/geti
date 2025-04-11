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

import { WorkInProgress } from './work-in-progress.component';

describe('WorkInProgress', () => {
    it('renders correctly without description', () => {
        render(<WorkInProgress />);

        expect(screen.getByText('We are working hard to get this up and running')).toBeInTheDocument();
    });

    it('renders correctly with description', () => {
        render(<WorkInProgress description='Some description' />);

        expect(screen.queryByText('We are working hard to get this up and running')).not.toBeInTheDocument();
        expect(screen.getByText('Some description')).toBeInTheDocument();
    });
});
