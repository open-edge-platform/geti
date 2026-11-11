// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { QueryFunctionContext } from '@tanstack/react-query';
import { getMockedMediaImage } from 'mocks/mock-media';

import { loadImageQueryOptions } from './use-load-image-query.hook';

describe('loadImageQueryOptions', () => {
    it('returns a placeholder for oversized media without downloading it', async () => {
        const fetchSpy = rs.spyOn(globalThis, 'fetch');
        const media = getMockedMediaImage({ width: 20000, height: 15000 });
        const { queryFn, queryKey } = loadImageQueryOptions('p1', media);

        const imageData = await queryFn?.({ queryKey, signal: new AbortController().signal } as QueryFunctionContext<
            typeof queryKey
        >);

        expect(imageData?.width).toBe(1);
        expect(imageData?.height).toBe(1);
        expect(fetchSpy).not.toHaveBeenCalled();
    });
});
