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

import { screen, within } from '@testing-library/react';

import { PartialPersonalAccessToken } from '../../../../core/personal-access-tokens/personal-access-tokens.interface';
import { formatUtcToLocal } from '../../../../shared/utils';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { PersonalAccessTokensTable } from './personal-access-tokens-table.component';

const getMockedToken = (token: Partial<PartialPersonalAccessToken> = {}): PartialPersonalAccessToken => ({
    id: 'token-id',
    name: 'token-name',
    description: 'token-description',
    expiresAt: '2125-03-18T15:23:12.380Z',
    organizationId: 'organization-id',
    userId: 'user-id',
    createdAt: '2025-03-17T15:23:12.380Z',
    partial: '"geti_pat_EKQbULMZ21U"',
    ...token,
});

describe('PersonalAccessTokensTable', () => {
    const renderComponent = (tokens: PartialPersonalAccessToken[]) => {
        return providersRender(<PersonalAccessTokensTable tokens={tokens} isLoading={false} />);
    };

    it('Does not display table when there are no tokens', () => {
        renderComponent([]);

        expect(screen.queryByLabelText('Personal Access Tokens table')).not.toBeInTheDocument();
    });

    it('Displays creation date, name, description and code', () => {
        const token = getMockedToken({
            name: 'Token 1',
            description: 'Token 1 description',
            partial: 'geti_pat_EKQbULMZ21U-1',
        });

        renderComponent([token]);

        // We don't want to have header row.
        const row = within(screen.getAllByRole('row')[1]);

        expect(row.getByText(formatUtcToLocal(token.createdAt, 'DD MMM YYYY'))).toBeInTheDocument();
        expect(row.getByText(formatUtcToLocal(token.expiresAt, 'DD MMM YYYY'))).toBeInTheDocument();
        expect(row.getByText(token.name)).toBeInTheDocument();
        expect(row.getByText(token.description)).toBeInTheDocument();
        expect(row.getByText(token.partial)).toBeInTheDocument();
        expect(row.queryByText('Expired')).not.toBeInTheDocument();
    });

    it('Displays expired token badge for expired token', () => {
        const token = getMockedToken({
            expiresAt: '2025-03-17T15:23:12.380Z',
        });

        renderComponent([token]);

        const row = within(screen.getAllByRole('row')[1]);

        expect(row.getByText('Expired')).toBeInTheDocument();
    });
});
