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

import { render } from '@testing-library/react';

import { getById } from '../../../../../test-utils/utils';
import { SortIcon } from './sort-icon.component';

describe('SortIcon', () => {
    it('renders ArrowUpIcon if the sort direction is "ASC"', () => {
        const { container } = render(<SortIcon sortDirection='ASC' />);

        expect(getById(container, 'arrow-up-icon')).toBeInTheDocument();
    });

    it('renders ArrowDownIcon if the sort direction is "DESC"', () => {
        const { container } = render(<SortIcon sortDirection='DESC' />);

        expect(getById(container, 'arrow-down-icon')).toBeInTheDocument();
    });

    it('renders nothing if the sort direction is "undefined"', () => {
        const { container } = render(<SortIcon sortDirection={undefined} />);

        expect(getById(container, 'arrow-up-icon')).not.toBeInTheDocument();
        expect(getById(container, 'arrow-down-icon')).not.toBeInTheDocument();

        expect(container.children).toHaveLength(0);
    });
});
