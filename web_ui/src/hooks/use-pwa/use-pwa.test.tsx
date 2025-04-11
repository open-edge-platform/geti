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

import { waitFor } from '@testing-library/react';

import { renderHookWithProviders } from '../../test-utils/render-hook-with-providers';
import { usePWA } from './use-pwa.hook';

describe('usePWA', () => {
    it('returns isPWAReady as `false` if there is no support for PWA', () => {
        const { result } = renderHookWithProviders(usePWA);

        expect(result.current.isPWAReady).toEqual(false);
    });

    it('returns isPWAReady as `true` if there is a service worker registered and is not using standalone app', async () => {
        Object.defineProperty(global.navigator, 'serviceWorker', {
            value: {
                ...global.navigator.serviceWorker,
                getRegistrations: async () => [{ active: { state: 'activated' } }],
            },
        });

        Object.defineProperty(global, 'matchMedia', {
            value: jest.fn().mockImplementation(() => ({
                matches: false,
            })),
        });

        const { result } = renderHookWithProviders(usePWA);

        await waitFor(() => {
            expect(result.current.isPWAReady).toEqual(true);
        });
    });
});
