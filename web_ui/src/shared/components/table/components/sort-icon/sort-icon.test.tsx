// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
