// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { instance as defaultAxiosInstance } from '../../../services/axios-instance';
import { CreateApiService } from '../../../services/create-api-service.interface';
import { API_URLS } from '../../../services/urls';
import { ProductDTO, ProductsResponseDTO } from '../dtos/products.interface';
import { Product, ProductsResponse } from '../products.interface';
import { GetProductsQueryOptions, ProductsService } from './products-service.interface';
import { getProductEntity, getProductsQueryOptionsDTO, getProductsResponseEntity } from './utils';

export const createApiProductsService: CreateApiService<ProductsService> = (
    { instance: platformInstance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getProducts = async (queryOptions: GetProductsQueryOptions): Promise<ProductsResponse> => {
        const { data } = await platformInstance.get<ProductsResponseDTO>(router.PRODUCTS(), {
            params: getProductsQueryOptionsDTO(queryOptions),
        });

        return getProductsResponseEntity(data);
    };

    const getProduct = async (productId: number): Promise<Product> => {
        const { data } = await platformInstance.get<ProductDTO>(router.PRODUCT(productId));

        return getProductEntity(data);
    };

    return {
        getProducts,
        getProduct,
    };
};
