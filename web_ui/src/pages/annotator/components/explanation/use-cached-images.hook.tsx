// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useState } from 'react';

import { useMutation } from '@tanstack/react-query';
import { isFunction } from 'lodash-es';

import { getImageData } from '../../../../shared/canvas-utils';
import { loadImage } from '../../../../shared/utils';

interface ImageSrc {
    src: string;
    image: ImageData;
}

interface useCachedImagesProps {
    formatter?: (image: ImageData) => Promise<ImageData>;
}

export const useCachedImages = ({ formatter }: useCachedImagesProps) => {
    const [images, setImages] = useState<ImageSrc[]>([]);

    const postProcessImage = async (image: ImageData) => (isFunction(formatter) ? formatter(image) : image);

    const mutation = useMutation({
        mutationFn: async (src: string) => {
            const existing = images.find((i) => i.src === src);

            if (existing) {
                return existing.image;
            }

            const image = await loadImage(src);

            return postProcessImage(getImageData(image));
        },
    });

    const { mutateAsync, isPending, data } = mutation;

    const load = useCallback(
        async (src: string | undefined) => {
            if (src) {
                const image = await mutateAsync(src);
                setImages((value) => [...value, { src, image }]);
            }
        },
        [setImages, mutateAsync]
    );

    return { load, image: data, isLoading: isPending };
};
