// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { getMediaItemBinaryUrl, getMediaItemKey, isOmePlane } from '../../../shared/media-item-utils';
import { renderOmeDemoPlane } from '../../../shared/ome-demo';
import { canRasteriseAtFullSize, loadImageData } from '../tools/utils';

export const loadImageQueryOptions = (projectId: string, media: Media) =>
    queryOptions({
        // An OME plane's pixels also depend on how its channels are displayed
        queryKey: ['mediaItem', projectId, getMediaItemKey(media), isOmePlane(media) ? media.channels : null],
        queryFn: async ({ signal }) => {
            if (isOmePlane(media)) {
                return renderOmeDemoPlane(media);
            }

            // Oversized media is displayed by an <img> instead (see tools/utils.ts), so downloading and decoding it
            // here would only produce a placeholder.
            if (!canRasteriseAtFullSize(media.width, media.height)) {
                return new ImageData(1, 1);
            }

            return loadImageData(getMediaItemBinaryUrl(projectId, media), signal);
        },
        staleTime: Infinity,
        retry: 0,
    });

export const useLoadImageQuery = (media: Media) => {
    const projectId = useProjectIdentifier();

    return useQuery({
        ...loadImageQueryOptions(projectId, media),
        placeholderData: keepPreviousData,
    });
};
