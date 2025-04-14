// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Environment, GPUProvider } from '../dto/utils.interface';
import { PlatformUtilsService, ProductInfoEntity } from './utils.interface';

export const createInMemoryPlatformUtilsService = (): PlatformUtilsService => {
    const getProductInfo = async (): Promise<ProductInfoEntity> => {
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

    return {
        getProductInfo,
    };
};
