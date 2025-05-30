// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import { Environment, ProductInfoEntityDTO } from '../dto/utils.interface';
import { PlatformUtilsService, ProductInfoEntity } from './utils.interface';

const isSmtpDefined = (val: string) => val === 'True';

export const createApiPlatformUtilsService: CreateApiService<PlatformUtilsService> = (
    { instance: platformInstance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getProductInfo = async (): Promise<ProductInfoEntity> => {
        const { data } = await platformInstance.get<ProductInfoEntityDTO>(router.PRODUCT_INFO);

        return {
            intelEmail: data['intel-email'],
            productVersion: data['product-version'],
            buildVersion: data['build-version'],
            isSmtpDefined: isSmtpDefined(data['smtp-defined']),
            environment: data?.environment || Environment.ON_PREM,
            grafanaEnabled: data?.grafana_enabled,
            gpuProvider: data['gpu-provider'],
        };
    };

    return {
        getProductInfo,
    };
};
