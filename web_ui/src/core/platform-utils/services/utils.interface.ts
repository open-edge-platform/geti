// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Environment, GPUProvider } from '../dto/utils.interface';

export interface ProductInfoEntity {
    isSmtpDefined: boolean;
    productVersion: string;
    buildVersion: string;
    intelEmail: string;
    environment: Environment;
    grafanaEnabled: boolean;
    gpuProvider: GPUProvider;
}

export type WorkflowId = string;

export interface PlatformUtilsService {
    getProductInfo: () => Promise<ProductInfoEntity>;
}
