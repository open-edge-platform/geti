// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import QUERY_KEYS from '../../../../../packages/core/src/requests/query-keys';
import { Product, ProductsResponse } from '../products.interface';

interface UseProductHook {
    useGetProductsQuery: () => UseQueryResult<ProductsResponse, AxiosError>;

    useGetProductQuery: (
        productId: number,
        options?: Pick<UseQueryOptions<Product, AxiosError>, 'enabled'>
    ) => UseQueryResult<Product, AxiosError>;
}

export const useProducts = (): UseProductHook => {
    const { productsService } = useApplicationServices();

    const useGetProductQuery: UseProductHook['useGetProductQuery'] = (
        productId,
        options = {}
    ): UseQueryResult<Product, AxiosError> => {
        return useQuery({
            queryKey: QUERY_KEYS.PRODUCT(productId),
            queryFn: () => {
                return productsService.getProduct(productId);
            },
            meta: { notifyOnError: true },
            ...options,
        });
    };

    const useGetProductsQuery: UseProductHook['useGetProductsQuery'] = () =>
        useQuery({
            queryKey: QUERY_KEYS.PRODUCTS,
            queryFn: () => productsService.getProducts({}),
            meta: { notifyOnError: true },
        });

    return {
        useGetProductsQuery,
        useGetProductQuery,
    };
};
