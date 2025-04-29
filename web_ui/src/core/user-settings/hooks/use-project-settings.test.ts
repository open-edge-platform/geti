// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, waitFor } from '@testing-library/react';
import { rest } from 'msw';

import { getMockedProjectIdentifier } from '../../../test-utils/mocked-items-factory/mocked-identifiers';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { server } from '../../annotations/services/test-utils';
import { apiRequestUrl } from '../../services/test-utils';
import { API_URLS } from '../../services/urls';
import { FEATURES_KEYS } from '../dtos/user-settings.interface';
import { UserProjectSettings } from '../services/user-settings.interface';
import { INITIAL_PROJECT_SETTINGS } from '../utils';
import { useUserProjectSettings } from './use-project-settings.hook';

const projectIdentifier = getMockedProjectIdentifier();

const USER_PROJECT_SETTINGS_URL = `api/${API_URLS.PROJECT_SETTINGS(projectIdentifier)}`;

describe('useProjectSettings', () => {
    it('returns initial project settings if there is no backend data', async () => {
        server.use(rest.get(USER_PROJECT_SETTINGS_URL, (_req, res, ctx) => res(ctx.status(204))));

        const { result } = renderHookWithProviders(() => useUserProjectSettings(projectIdentifier), {
            providerProps: { useInMemoryEnvironment: false },
        });

        await waitFor(() => {
            expect(result.current.config).toEqual(INITIAL_PROJECT_SETTINGS);
        });
    });

    it('returns project settings from the backend', async () => {
        const projectSettings: UserProjectSettings = {
            ...INITIAL_PROJECT_SETTINGS,
            [FEATURES_KEYS.COUNTING_PANEL]: {
                title: 'Counting',
                isEnabled: true,
                tooltipDescription: 'Show counting list on the right sidebar',
            },
        };

        server.use(
            rest.get(apiRequestUrl(USER_PROJECT_SETTINGS_URL), (_req, res, ctx) =>
                res(ctx.status(200), ctx.json({ settings: JSON.stringify(projectSettings) }))
            )
        );

        const { result } = renderHookWithProviders(() => useUserProjectSettings(projectIdentifier), {
            providerProps: { useInMemoryEnvironment: false },
        });

        await waitFor(() => {
            expect(result.current.config).toEqual(projectSettings);
        });
    });

    it('save global settings to the backend', async () => {
        const projectSettings: UserProjectSettings = {
            ...INITIAL_PROJECT_SETTINGS,
            [FEATURES_KEYS.COUNTING_PANEL]: {
                title: 'Counting',
                isEnabled: true,
                tooltipDescription: 'Show counting list on the right sidebar',
            },
        };

        server.use(rest.get(USER_PROJECT_SETTINGS_URL, (_req, res, ctx) => res(ctx.status(204))));

        server.use(
            rest.post(USER_PROJECT_SETTINGS_URL, (req, res, ctx) => {
                expect(req.body).toEqual({ settings: JSON.stringify(projectSettings) });

                return res(ctx.status(200));
            })
        );

        const { result } = renderHookWithProviders(() => useUserProjectSettings(projectIdentifier), {
            providerProps: { useInMemoryEnvironment: false },
        });

        await waitFor(() => {
            expect(result.current.config).toEqual(INITIAL_PROJECT_SETTINGS);
        });

        await act(async () => {
            await result.current.saveConfig(projectSettings);
        });
    });
});
