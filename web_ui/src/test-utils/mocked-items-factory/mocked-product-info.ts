// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Environment, GPUProvider } from '../../core/platform-utils/dto/utils.interface';
import { ProductInfoEntity } from '../../core/platform-utils/services/utils.interface';

export const getMockedProductInfo = (productInfo: Partial<ProductInfoEntity> = {}): ProductInfoEntity => ({
    productVersion: '1.6.0',
    buildVersion: '1.6.0.test.123123',
    isSmtpDefined: true,
    grafanaEnabled: false,
    gpuProvider: GPUProvider.INTEL,
    intelEmail: 'support@geti.com',
    environment: Environment.ON_PREM,
    ...productInfo,
});
