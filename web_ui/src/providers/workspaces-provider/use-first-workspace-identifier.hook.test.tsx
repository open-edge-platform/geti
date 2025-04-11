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

import { ReactNode } from 'react';

import { waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';

import { renderHookWithProviders } from '../../test-utils/render-hook-with-providers';
import { paths } from './../../core/services/routes';
import { useFirstWorkspaceIdentifier } from './use-first-workspace-identifier.hook';

describe('useFirstWorkspaceIdentifier', () => {
    const Wrapper = ({ children }: { children: ReactNode }) => {
        const Element = <>{children}</>;
        return (
            <Routes>
                <Route path={paths.workspace.pattern} element={Element} />
                <Route path={paths.organization.index.pattern} element={Element} />
                <Route path={paths.account.profile.pattern} element={Element} />
            </Routes>
        );
    };

    it('Returns the currently used workspace id', async () => {
        const { result } = renderHookWithProviders(useFirstWorkspaceIdentifier, {
            providerProps: {
                initialEntries: ['/organizations/xxx/workspaces/yyy'],
            },
            wrapper: Wrapper,
        });

        await waitFor(() => {
            expect(result.current).not.toBeNull();
        });

        expect(result.current).toEqual({ organizationId: 'xxx', workspaceId: 'yyy' });
    });

    it('Returns the first available workspace id', async () => {
        const { result } = renderHookWithProviders(useFirstWorkspaceIdentifier, {
            providerProps: {
                initialEntries: ['/organizations/xxx/'],
            },
            wrapper: Wrapper,
        });

        expect(result.current).toBeNull();

        await waitFor(() => {
            expect(result.current).not.toBeNull();
        });

        expect(result.current).toEqual({ organizationId: 'xxx', workspaceId: 'workspace-id' });
    });
});
