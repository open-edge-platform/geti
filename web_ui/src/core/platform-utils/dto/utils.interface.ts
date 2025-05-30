// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum Environment {
    SAAS = 'saas',
    ON_PREM = 'on-prem',
}

export enum GPUProvider {
    NONE = 'none',
    INTEL = 'intel',
    NVIDIA = 'nvidia',
}

export interface ProductInfoEntityDTO {
    'intel-email': string;
    'product-version': string;
    'build-version': string;
    'smtp-defined': string;
    'gpu-provider': GPUProvider;
    grafana_enabled: boolean;
    environment?: Environment;
}
