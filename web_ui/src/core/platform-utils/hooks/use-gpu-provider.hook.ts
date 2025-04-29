// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { GPUProvider } from '../dto/utils.interface';
import { usePlatformUtils } from './use-platform-utils.hook';

export const useGpuProvider = () => {
    const { useProductInfo } = usePlatformUtils();

    const productInfo = useProductInfo();

    return productInfo.data?.gpuProvider || GPUProvider.NONE;
};
