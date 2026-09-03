// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ThemeProvider } from '@geti-ui/ui';
import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';

import { queryClient } from './query-client/query-client';
import { router } from './router';

export const Providers = () => {
    return (
        <QueryClientProvider client={queryClient}>
            {/* ThemeProvider defaults to en-US; follow the user's system locale for date and number formatting */}
            <ThemeProvider router={router} locale={navigator.language}>
                <RouterProvider
                    router={router}
                    future={{
                        v7_startTransition: true,
                    }}
                />
            </ThemeProvider>
        </QueryClientProvider>
    );
};
