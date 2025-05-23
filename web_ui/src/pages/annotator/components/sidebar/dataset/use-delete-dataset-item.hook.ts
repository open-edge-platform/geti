// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useState } from 'react';

import { useNavigateToAnnotatorRoute } from '@geti/core/src/services/use-navigate-to-annotator-route.hook';
import { isEmpty, isEqual } from 'lodash-es';

import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideo } from '../../../../../core/media/video.interface';
import { isAnomalyDomain } from '../../../../../core/projects/domains';
import { useDeleteMediaMutation } from '../../../../media/hooks/media-delete/media-delete.hook';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { useDataset } from '../../../providers/dataset-provider/dataset-provider.component';
import { useIsInActiveMode } from '../../../providers/dataset-provider/use-is-in-active-mode.hook';
import { useSelectedMediaItem } from '../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { getMediaItemToSelect } from '../../main-content/use-select-first-media-item.hook';

interface UseDeleteDatasetItem {
    mediaItem: MediaItem;
    isSelected: boolean;
}

export const useDeleteDatasetItem = ({ mediaItem, isSelected }: UseDeleteDatasetItem) => {
    const [dialogKey, setDialogKey] = useState<Key | undefined>(undefined);
    const { isSingleDomainProject, isTaskChainProject } = useProject();
    const { selectedTask } = useTask();
    const isAnomalyVideo = isVideo(mediaItem) && isSingleDomainProject(isAnomalyDomain);
    const datasetIdentifier = useDatasetIdentifier();
    const { datasetId, workspaceId, projectId, organizationId } = datasetIdentifier;
    const isActiveMode = useIsInActiveMode();
    const { deleteMedia } = useDeleteMediaMutation();
    const { setSelectedMediaItem } = useSelectedMediaItem();

    const navigate = useNavigateToAnnotatorRoute();

    const { refetchMedia, mediaItemsQuery } = useDataset();

    const handleDelete = async () => {
        deleteMedia.mutate([mediaItem], {
            onSuccess: async () => {
                const mediaItems = (mediaItemsQuery.data?.pages?.flatMap(({ media }) => media) ?? []).filter(
                    (item) => !isEqual(item, mediaItem)
                );

                // deleted selected media was not the last one
                if (!isEmpty(mediaItems) && isSelected) {
                    setSelectedMediaItem(getMediaItemToSelect(mediaItems));
                }

                // deleted media was the last one
                if (isEmpty(mediaItems)) {
                    setSelectedMediaItem(undefined);

                    navigate({
                        datasetIdentifier: { organizationId, projectId, workspaceId, datasetId },
                        mediaItem: undefined,
                        active: isActiveMode,
                        taskId: isTaskChainProject ? selectedTask?.id : undefined,
                    });
                }

                !isAnomalyVideo && (await refetchMedia());
            },
        });
    };

    return {
        dialogKey,
        setDialogKey,
        isAnomalyVideo,
        handleDelete,
    };
};
