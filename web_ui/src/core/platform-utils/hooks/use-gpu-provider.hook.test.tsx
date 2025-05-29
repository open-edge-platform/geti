// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';

import { getMockedProductInfo } from '../../../test-utils/mocked-items-factory/mocked-product-info';
import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { GPUProvider } from '../dto/utils.interface';
import { createInMemoryPlatformUtilsService } from '../services/create-in-memory-platform-utils-service';
import { useGpuProvider } from './use-gpu-provider.hook';

describe('useGpuProvider Hook', () => {
    const wrapper = ({ children }: { children?: ReactNode }) => {
        const platformUtilsService = createInMemoryPlatformUtilsService();
        platformUtilsService.getProductInfo = () =>
            Promise.resolve(
                getMockedProductInfo({
                    gpuProvider: GPUProvider.INTEL,
                })
            );

        return <RequiredProviders platformUtilsService={platformUtilsService}>{children}</RequiredProviders>;
    };

    it('returns the value of the current gpu provider', async () => {
        const { result } = renderHook(() => useGpuProvider(), { wrapper });

        await waitFor(() => {
            expect(result.current).toBe(GPUProvider.INTEL);
        });
    });
});
