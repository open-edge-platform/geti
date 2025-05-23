// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, waitFor } from '@testing-library/react';
import { rest } from 'msw';

import { apiRequestUrl } from '../../../../packages/core/src/services/test-utils';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { server } from '../../annotations/services/test-utils';
import { API_URLS } from '../../services/urls';
import { GENERAL_SETTINGS_KEYS } from '../dtos/user-settings.interface';
import { INITIAL_GLOBAL_SETTINGS } from '../utils';
import { useUserGlobalSettings } from './use-global-settings.hook';

const USER_GLOBAL_SETTINGS_URL = `api/${API_URLS.GLOBAL_SETTINGS()}`;

describe('useUserGlobalSettings', () => {
    it('returns initial global settings if there is no backend data', async () => {
        server.use(rest.get(USER_GLOBAL_SETTINGS_URL, (_req, res, ctx) => res(ctx.status(204))));

        const { result } = renderHookWithProviders(() => useUserGlobalSettings(), {
            providerProps: { useInMemoryEnvironment: false },
        });

        await waitFor(() => {
            expect(result.current.config).toEqual(INITIAL_GLOBAL_SETTINGS);
        });
    });

    it('returns global settings from the backend', async () => {
        const globalSettings = {
            ...INITIAL_GLOBAL_SETTINGS,
            [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
                wasDismissed: true,
                window: {
                    start: 1711312113376,
                    end: 1711513116880,
                },
            },
        };

        server.use(
            rest.get(apiRequestUrl(USER_GLOBAL_SETTINGS_URL), (_req, res, ctx) =>
                res(ctx.status(200), ctx.json({ settings: JSON.stringify(globalSettings) }))
            )
        );

        const { result } = renderHookWithProviders(() => useUserGlobalSettings(), {
            providerProps: { useInMemoryEnvironment: false },
        });

        await waitFor(() => {
            expect(result.current.config).toEqual(globalSettings);
        });
    });

    it('save global settings to the backend', async () => {
        const globalSettings = {
            ...INITIAL_GLOBAL_SETTINGS,
            [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
                wasDismissed: true,
                window: {
                    start: 1711312113376,
                    end: 1711513116880,
                },
            },
        };

        server.use(rest.get(USER_GLOBAL_SETTINGS_URL, (_req, res, ctx) => res(ctx.status(204))));

        server.use(
            rest.post(USER_GLOBAL_SETTINGS_URL, (req, res, ctx) => {
                expect(req.body).toEqual({ settings: JSON.stringify(globalSettings) });

                return res(ctx.status(200));
            })
        );

        const { result } = renderHookWithProviders(() => useUserGlobalSettings(), {
            providerProps: { useInMemoryEnvironment: false },
        });

        await waitFor(() => {
            expect(result.current.config).toEqual(INITIAL_GLOBAL_SETTINGS);
        });

        await act(async () => {
            await result.current.saveConfig(globalSettings);
        });
    });
});
