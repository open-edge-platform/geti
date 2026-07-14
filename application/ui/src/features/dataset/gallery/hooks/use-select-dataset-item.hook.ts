// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from 'react';

import type { Media } from '@/api/types';
import { useDatasetMediaWithReviewStatus } from 'hooks/use-dataset-media-with-review-status.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { useLocation, useNavigate, useParams } from 'react-router';

import { paths } from '../../../../constants/paths';
import { isVideo, isVideoFrame } from '../../../../shared/media-item-utils';
import { useGetDatasetMediaItem } from '../../api/use-get-dataset-media-item';

const useFetchMediaItemsUntilSelectedMediaIsPresent = ({
    selectedMediaInTheFetchedList,
}: {
    selectedMediaInTheFetchedList: Media | null;
}) => {
    const { fetchNextPage } = useDatasetMediaWithReviewStatus();

    useEffect(() => {
        if (selectedMediaInTheFetchedList) {
            return;
        }

        fetchNextPage();
    }, [selectedMediaInTheFetchedList, fetchNextPage]);
};

export const useSelectDatasetItem = () => {
    const navigate = useNavigate();
    const { search } = useLocation();
    const projectId = useProjectIdentifier();
    const { items } = useDatasetMediaWithReviewStatus();
    const { datasetItemId: selectedDatasetItemId } = useParams<{ datasetItemId: string }>();

    const selectedMediaInTheFetchedList = items.find((item) => item.id === selectedDatasetItemId) ?? null;

    const {
        mediaItem: fetchedMediaItem,
        isPending: isFetchPending,
        isError,
        errorMessage,
    } = useGetDatasetMediaItem(selectedDatasetItemId, {
        enabled: selectedDatasetItemId != null && selectedMediaInTheFetchedList === null,
    });

    useFetchMediaItemsUntilSelectedMediaIsPresent({ selectedMediaInTheFetchedList });

    const selectedMediaItem = selectedMediaInTheFetchedList ?? fetchedMediaItem ?? null;

    const isResolving = selectedDatasetItemId != null && selectedMediaItem === null && isFetchPending && !isError;
    const fetchErrorMessage =
        selectedDatasetItemId != null && selectedMediaItem === null && isError ? errorMessage : null;

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

    return {
        selectedMediaItem,
        selectedDatasetItemId,
        isResolving,
        fetchErrorMessage,
        onSelectedMediaItemChange,
    };
};
