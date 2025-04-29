// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
