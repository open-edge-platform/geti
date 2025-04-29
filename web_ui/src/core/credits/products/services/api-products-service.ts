// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
