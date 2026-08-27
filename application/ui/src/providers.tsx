// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ThemeProvider } from '@geti-ui/ui';
import { QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import { RouterProvider } from 'react-router-dom';

import { i18n } from './i18n';
import { queryClient } from './query-client/query-client';
import { router } from './router';

export const Providers = () => {
    return (
        <I18nextProvider i18n={i18n}>
            <QueryClientProvider client={queryClient}>
                <ThemeProvider router={router}>
                    <RouterProvider
                        router={router}
                        future={{
                            v7_startTransition: true,
                        }}
                    />
                </ThemeProvider>
            </QueryClientProvider>
        </I18nextProvider>
    );
};
