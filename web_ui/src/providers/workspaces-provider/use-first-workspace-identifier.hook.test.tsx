// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { paths } from '@geti/core';
import { waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';

import { renderHookWithProviders } from '../../test-utils/render-hook-with-providers';
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
