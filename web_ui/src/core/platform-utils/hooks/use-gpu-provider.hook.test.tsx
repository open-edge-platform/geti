// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';

import { RequiredProviders } from '../../../test-utils/required-providers-render';
import { Environment, GPUProvider } from '../dto/utils.interface';
import { createInMemoryPlatformUtilsService } from '../services/create-in-memory-platform-utils-service';
import { ProductInfoEntity } from '../services/utils.interface';
import { useGpuProvider } from './use-gpu-provider.hook';

describe('useGpuProvider Hook', () => {
    const mockGetProductInfo = async (): Promise<ProductInfoEntity> => {
        return {
            productVersion: '1.6.0',
            grafanaEnabled: false,
            gpuProvider: GPUProvider.INTEL,
            buildVersion: '1.6.0.test.123123',
            isSmtpDefined: true,
            intelEmail: 'support@geti.com',
            environment: Environment.ON_PREM,
        };
    };

    const wrapper = ({ children }: { children?: ReactNode }) => {
        const platformUtilsService = createInMemoryPlatformUtilsService();
        platformUtilsService.getProductInfo = mockGetProductInfo;

        return <RequiredProviders platformUtilsService={platformUtilsService}>{children}</RequiredProviders>;
    };

    it('returns the value of the current gpu provider', async () => {
        const { result } = renderHook(() => useGpuProvider(), { wrapper });

        expect(result.current).toBe(GPUProvider.NONE);

        await waitFor(() => {
            expect(result.current).toBe(GPUProvider.INTEL);
        });
    });
});
