// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen } from '@testing-library/react';

import { UsersCount } from './users-count.component';

describe('UsersCount', () => {
    it('Show amount of users without filters', () => {
        render(<UsersCount totalMatchedCount={3} totalCount={5} hasFilters={false} />);

        expect(screen.getByText('5 users')).toBeVisible();
    });

    it('Show filtered amount of users', () => {
        render(<UsersCount totalMatchedCount={1} totalCount={5} hasFilters={true} />);

        expect(screen.getByText('1 out of 5 users')).toBeVisible();
    });
});
