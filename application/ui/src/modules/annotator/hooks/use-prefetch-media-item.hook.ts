// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from 'react';

import type { Media } from '@/api/types';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { isOmeImage } from '../../../shared/media-item-utils';
import { annotationsQueryOptions } from '../shell/api/use-annotations-query';
import { loadImageQueryOptions } from './use-load-image-query.hook';

// Fetching the annotations dominates the transition between media items, and the media binary queues behind it
export const usePrefetchMediaItem = (mediaItem: Media | undefined) => {
    const projectId = useProjectIdentifier();
    const queryClient = useQueryClient();

    useEffect(() => {
        // OME images are only displayed plane by plane, so there is nothing generic to prefetch
        if (mediaItem === undefined || isOmeImage(mediaItem)) {
            return;
        }

        void queryClient.prefetchQuery(annotationsQueryOptions(projectId, mediaItem));
        void queryClient.prefetchQuery(loadImageQueryOptions(projectId, mediaItem));
    }, [mediaItem, projectId, queryClient]);
};
