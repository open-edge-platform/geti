// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { getMediaItemImageUrl, getMediaItemKey, isOmePlane } from '../../../shared/media-item-utils';
import { canRasteriseAtFullSize, loadImageData } from '../tools/utils';

export const loadImageQueryOptions = (projectId: string, media: Media) => {
    const url = getMediaItemImageUrl(projectId, media);

    return queryOptions({
        queryKey: ['mediaItem', projectId, getMediaItemKey(media), url],
        queryFn: async ({ signal }) => {
            // Oversized media is displayed by an <img> instead (see tools/utils.ts), so downloading and decoding it
            // here would only produce a placeholder.
            if (!canRasteriseAtFullSize(media.width, media.height)) {
                return new ImageData(1, 1);
            }

            return loadImageData(url, signal);
        },
        staleTime: Infinity,
        // Every channel view tweak renders a new plane, so unused ones are dropped right away
        ...(isOmePlane(media) && { gcTime: 0 }),
        retry: 0,
    });
};

export const useLoadImageQuery = (media: Media) => {
    const projectId = useProjectIdentifier();

    return useQuery({
        ...loadImageQueryOptions(projectId, media),
        placeholderData: keepPreviousData,
    });
};
