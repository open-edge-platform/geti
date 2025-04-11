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
