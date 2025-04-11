// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useCallback, useState } from 'react';

import { useMutation } from '@tanstack/react-query';
import isFunction from 'lodash/isFunction';

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
