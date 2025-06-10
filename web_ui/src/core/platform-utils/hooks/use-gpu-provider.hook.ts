// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { GPUProvider } from '../dto/utils.interface';
import { useProductInfo } from './use-platform-utils.hook';

export const useGpuProvider = () => {
    const productInfo = useProductInfo();

    return productInfo.data?.gpuProvider || GPUProvider.NONE;
};
