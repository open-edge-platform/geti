// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
