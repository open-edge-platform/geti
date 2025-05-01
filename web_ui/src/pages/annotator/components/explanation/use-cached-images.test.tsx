// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import * as utils from '@shared/utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook } from '@testing-library/react';

import Antelope from '../../../../assets/tests-assets/antelope.webp';
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
