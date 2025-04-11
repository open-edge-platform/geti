// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
