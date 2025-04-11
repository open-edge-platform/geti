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

import { useMemo } from 'react';

import { createBrowserRouter, createRoutesFromElements, RouterProvider } from 'react-router-dom';

import { useFeatureFlags } from './core/feature-flags/hooks/use-feature-flags.hook';
import { appRoutes } from './routes/app-routes.component';
import { intelAdminRoutes } from './routes/intel-admin-routes';
import { IntelBrandedLoading } from './shared/components/loading/intel-branded-loading.component';
import { ThemeProvider } from './theme/theme-provider.component';

export const IS_ADMIN_BUILD =
    process.env.REACT_APP_BUILD_TARGET === 'admin' || process.env.REACT_APP_BUILD_TARGET === 'admin_standalone';

export const App = (): JSX.Element => {
    // Load feature flags at the top of the tree leveraging the suspense.
    useFeatureFlags();

    const router = useMemo(() => {
        const routes = process.env.REACT_APP_INCLUDE_ALL_ROUTES
            ? [appRoutes(), intelAdminRoutes()]
            : IS_ADMIN_BUILD
              ? [intelAdminRoutes()]
              : [appRoutes()];

        return createBrowserRouter(createRoutesFromElements(routes));
    }, []);

    return (
        <ThemeProvider router={router}>
            <RouterProvider router={router} fallbackElement={<IntelBrandedLoading />} />
            <div id='custom-notification'></div>
        </ThemeProvider>
    );
};
