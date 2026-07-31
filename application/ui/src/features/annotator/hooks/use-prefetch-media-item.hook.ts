// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from 'react';

import type { Media } from '@/api/types';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { annotationsQueryOptions } from '../../dataset/media-preview/api/use-annotations-query';
import { loadImageQueryOptions } from './use-load-image-query.hook';

// Fetching the annotations dominates the transition between media items, and the media binary queues behind it
export const usePrefetchMediaItem = (mediaItem: Media | undefined) => {
    const projectId = useProjectIdentifier();
    const queryClient = useQueryClient();

    useEffect(() => {
        if (mediaItem === undefined) {
            return;
        }

        void queryClient.prefetchQuery(annotationsQueryOptions(projectId, mediaItem));
        void queryClient.prefetchQuery(loadImageQueryOptions(projectId, mediaItem));
    }, [mediaItem, projectId, queryClient]);
};
