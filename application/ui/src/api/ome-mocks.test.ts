// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from '@rstest/core';

import { API_BASE_URL } from './client';

describe('OME plane listing mock', () => {
    it.each([
        ['', { limit: 50, offset: 0, total: 0, count: 0 }],
        ['?z=12&t=0&limit=2&offset=8', { limit: 2, offset: 8, total: 0, count: 0 }],
    ])('returns deterministic pagination for %s', async (query, pagination) => {
        const baseUrl = API_BASE_URL || window.location.origin;
        const response = await fetch(
            `${baseUrl}/api/projects/00000000-0000-0000-0000-000000000001/dataset/media/00000000-0000-0000-0000-000000000002/planes${query}`
        );

        expect(response.status).toBe(200);
        expect(await response.json()).toEqual({ items: [], pagination });
    });
});
