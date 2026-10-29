// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { getMediaItemBinaryUrl, getMediaItemKey } from '../../../shared/media-item-utils';
import { getImageData, loadImage } from '../tools/utils';

export const loadImageQueryOptions = (projectId: string, media: Media) =>
    queryOptions({
        queryKey: ['mediaItem', projectId, getMediaItemKey(media)],
        queryFn: async () => {
            const image = await loadImage(getMediaItemBinaryUrl(projectId, media));

            return getImageData(image);
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
