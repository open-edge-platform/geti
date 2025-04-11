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

import { useMutation } from '@tanstack/react-query';

import { AlgorithmType } from '../../../../hooks/use-load-ai-webworker/algorithm.interface';
import { useLoadAIWebworker } from '../../../../hooks/use-load-ai-webworker/use-load-ai-webworker.hook';

export const useInferenceImage = (width: number, height: number) => {
    const { worker } = useLoadAIWebworker(AlgorithmType.INFERENCE_IMAGE);

    const mutation = useMutation({
        mutationFn: async (image: ImageData) => {
            if (worker) {
                const instance = await new worker.InferenceImage();

                return instance.resize(image, width, height);
            } else {
                return Promise.reject('Unable to run inference mutation');
            }
        },
    });

    return async (imageData: ImageData) => mutation.mutateAsync(imageData);
};
