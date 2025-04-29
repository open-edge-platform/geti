// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { OrganizationBalance } from '../../../../core/credits/credits.interface';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { Balance } from './balance.component';

describe('RenewableAmount', () => {
    const renderApp = (props: { isLoading: boolean; organizationBalance?: OrganizationBalance }) => {
        render(<Balance {...props} />);
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loading response', () => {
        renderApp({ isLoading: true });
        expect(screen.getByLabelText('Loading...')).toBeInTheDocument();
    });

    it('render recurring credits', async () => {
        const organizationBalance = { available: 10, incoming: 20, blocked: 0 };
        renderApp({ isLoading: false, organizationBalance });

        expect(screen.getByLabelText('available')).toHaveTextContent(`${organizationBalance.available}`);
        expect(screen.getByLabelText('incoming')).toHaveTextContent(`of ${organizationBalance.incoming}`);
        expect(screen.queryByLabelText('blocked')).not.toBeInTheDocument();
    });

    it('render recurring credits with pending', async () => {
        const organizationBalance = { available: 10, incoming: 20, blocked: 5 };
        renderApp({ isLoading: false, organizationBalance });

        expect(screen.getByLabelText('available')).toHaveTextContent(`${organizationBalance.available}`);
        expect(screen.getByLabelText('incoming')).toHaveTextContent(`of ${organizationBalance.incoming}`);
        expect(screen.getByLabelText('pending')).toHaveTextContent(`(${organizationBalance.blocked} pending)`);
    });

    it('balance is null', async () => {
        renderApp({ isLoading: false });

        expect(screen.queryByLabelText('incoming')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('available')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('pending')).not.toBeInTheDocument();
    });
});
