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

import { ReactNode } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook } from '@testing-library/react';

import Antelope from '../../../../assets/tests-assets/antelope.webp';
import * as utils from '../../../../shared/utils';
import { useCachedImages } from './use-cached-images.hook';

const loadImage = jest.spyOn(utils, 'loadImage');

const wrapper = ({ children }: { children?: ReactNode }) => {
    return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>;
};

describe('useCachedImages', () => {
    beforeEach(() => {
        (loadImage as jest.Mock).mockReset();
    });

    it('loads image to HTMLImageElement', async () => {
        const { result } = renderHook(() => useCachedImages({}), { wrapper });

        await act(async () => await result.current.load(Antelope));

        expect(loadImage).toBeCalledWith(Antelope);
    });

    it('does not load the same url twice', async () => {
        const { result } = renderHook(() => useCachedImages({}), { wrapper });

        await act(async () => await result.current.load(Antelope));
        await act(async () => await result.current.load(Antelope));

        expect(loadImage).toBeCalledTimes(1);
    });

    it('loads url and returns image', async () => {
        (loadImage as jest.Mock).mockRestore();
        const { result } = renderHook(() => useCachedImages({}), { wrapper });

        await act(async () => await result.current.load(Antelope));

        expect(result.current.image).not.toBeUndefined();
    });
});
