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

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { UsersHeader } from './users-header.component';

describe('UsersHeader', () => {
    it('Check all users header elements', async () => {
        render(
            <UsersHeader
                totalMatchedCount={2}
                totalCount={3}
                hasFilterOptions={false}
                setUsersQueryParams={jest.fn()}
            />
        );

        expect(screen.getByTestId('users-header-search-field')).toBeInTheDocument();
        expect(screen.getByTestId('users-header-role-picker')).toBeInTheDocument();
        expect(screen.getByTestId('users-header-users-count')).toBeInTheDocument();
    });
});
