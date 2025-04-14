// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { rest } from 'msw';

import { server } from '../../annotations/services/test-utils';
import { apiRequestUrl } from '../../services/test-utils';
import { API_URLS } from '../../services/urls';
import { createApiFeatureFlagService } from './api-feature-flag-service';

describe('FeatureFlagService', () => {
    const featureFlagUrl = API_URLS.FEATURE_FLAGS;
    const service = createApiFeatureFlagService();

    it('success case', async () => {
        server.use(
            rest.get(apiRequestUrl(featureFlagUrl), (_req, res, ctx) => {
                return res(ctx.json({ FEATURE_FLAG_TEST_FEATURE_1: true, FEATURE_FLAG_TEST_FEATURE_2: false }));
            })
        );

        const response = await service.getFeatureFlags();

        expect(response).toEqual({ FEATURE_FLAG_TEST_FEATURE_1: true, FEATURE_FLAG_TEST_FEATURE_2: false });
    });

    it('error case', async () => {
        server.use(
            rest.get(apiRequestUrl(featureFlagUrl), (_req, res, ctx) => {
                return res(
                    ctx.status(404),
                    ctx.json({
                        error_code: 'feature_flags_not_found',
                        http_status: 404,
                        message: 'Something went wrong',
                    })
                );
            })
        );

        await expect(service.getFeatureFlags()).rejects.toThrow('Something went wrong');
    });
});
