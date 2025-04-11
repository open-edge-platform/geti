// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen } from '@testing-library/react';

import { JobsIconWithNumber } from './jobs-icon-with-number.component';

describe('jobs icon with number component', () => {
    it('check if number of running jobs is properly shown', () => {
        render(<JobsIconWithNumber runningJobs={7} />);
        expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('Check if there is icon displayed', () => {
        render(<JobsIconWithNumber runningJobs={7} />);
        expect(screen.getByLabelText('tasks in progress')).toBeInTheDocument();
    });
});
