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
