// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
