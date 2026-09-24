// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { PointerEvent, SVGProps } from 'react';

import type { Media, MediaWithPagination } from '@/api/types';
import { InfiniteData, QueryClient } from '@tanstack/react-query';

import { isLeftButton, isWheelButton } from '../../shared/buttons-utils';
import { isVideo } from '../../shared/media-item-utils';

type OnPointerDown = SVGProps<SVGElement>['onPointerDown'];
export const allowPanning = (onPointerDown?: OnPointerDown): OnPointerDown | undefined => {
    if (onPointerDown === undefined) {
        return;
    }

    return (event: PointerEvent<SVGElement>) => {
        const isPressingPanningHotKeys = (isLeftButton(event) && event.ctrlKey) || isWheelButton(event);

        if (isPressingPanningHotKeys) {
            return;
        }

        return onPointerDown(event);
    };
};

export const DEFAULT_ANNOTATION_STYLES = {
    fillOpacity: 'var(--annotation-fill-opacity)',
    fill: 'var(--annotation-fill)',
    stroke: 'var(--annotation-stroke)',
    strokeLinecap: 'round',
    strokeWidth: 'calc(3px / var(--zoom-scale))',
    strokeDashoffset: 0,
    strokeDasharray: 0,
    strokeOpacity: 'var(--annotation-border-opacity, 1)',
} satisfies SVGProps<SVGElement>;

export const incrementCachedAnnotatedFrameCount = (queryClient: QueryClient, mediaItem: Media) => {
    queryClient.setQueriesData<InfiniteData<MediaWithPagination>>(
        { queryKey: ['get', '/api/projects/{project_id}/dataset/media'] },
        (oldData) => {
            if (!oldData?.pages) return oldData;

            return {
                ...oldData,
                pages: oldData.pages.map((page) => ({
                    ...page,
                    items: page.items.map((item) =>
                        isVideo(item) && item.id === mediaItem.id
                            ? { ...item, annotated_frame_count: item.annotated_frame_count + 1 }
                            : item
                    ),
                })),
            };
        }
    );
};
