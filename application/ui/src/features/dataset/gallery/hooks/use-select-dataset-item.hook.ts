// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useMemo, useRef } from 'react';

import type { Media } from '@/api/types';
import { useDatasetMediaWithReviewStatus } from 'hooks/use-dataset-media-with-review-status.hook';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { paths } from '../../../../constants/paths';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier.hook';
import { isVideo, isVideoFrame } from '../../../../shared/media-item-utils';

export const useSelectDatasetItem = () => {
    const navigate = useNavigate();
    const { search } = useLocation();
    const projectId = useProjectIdentifier();
    const { items } = useDatasetMediaWithReviewStatus();
    const { datasetItemId: selectedDatasetItemId } = useParams<{ datasetItemId: string }>();

    const prevSelectedMediaItem = useRef<Media | null>(null);

    // This state determines the currently displayed media item in the annotator.
    // It is computed based on the `selectedDatasetItemId` param and the `items` list.
    // If the `selectedDatasetItemId` is not found in the `items` list, we keep the previously selected media item.
    // This can happen when filters change (e.g. opening an annotated item and then filtering by
    // "Media with missing annotations"), which would otherwise close the annotator unexpectedly.
    const selectedMediaItem = useMemo(() => {
        if (selectedDatasetItemId === undefined) {
            return null;
        }

        const newSelectedMediaItem = items.find((item) => item.id === selectedDatasetItemId);

        if (newSelectedMediaItem === undefined) {
            return prevSelectedMediaItem.current?.id === selectedDatasetItemId ? prevSelectedMediaItem.current : null;
        }

        return newSelectedMediaItem;
    }, [selectedDatasetItemId, items]);

    useEffect(() => {
        prevSelectedMediaItem.current = selectedMediaItem;
    }, [selectedMediaItem]);

    const onSelectedMediaItemChange = (item: Media | null) => {
        if (item === null) {
            navigate({ pathname: paths.project.dataset.index({ projectId }), search });
            return;
        }

        if (isVideo(item)) {
            navigate({
                pathname: paths.project.dataset.item.frame({ projectId, datasetItemId: item.id, frameNumber: '0' }),
                search,
            });
            return;
        }

        if (isVideoFrame(item)) {
            navigate({
                pathname: paths.project.dataset.item.frame({
                    projectId,
                    datasetItemId: item.id,
                    frameNumber: item.frame_number.toString(),
                }),
                search,
            });
            return;
        }

        navigate({ pathname: paths.project.dataset.item.index({ projectId, datasetItemId: item.id }), search });
    };

    return { selectedMediaItem, onSelectedMediaItemChange };
};
