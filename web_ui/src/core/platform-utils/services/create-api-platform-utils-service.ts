// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { Environment, ProductInfoEntityDTO } from '../dto/utils.interface';
import { PlatformUtilsService, ProductInfoEntity } from './utils.interface';

const isSmtpDefined = (val: string) => val === 'True';

export const createApiPlatformUtilsService: CreateApiService<PlatformUtilsService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
