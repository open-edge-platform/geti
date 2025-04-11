// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key } from 'react';

import { MediaItem } from '../../../../../core/media/media.interface';
import { useNavigateToAnnotatorRoute } from '../../../../../core/services/use-navigate-to-annotator-route.hook';
import { MediaItemMenuActions } from '../../../../../shared/components/media-item-menu-with-deletion/media-item-menu-actions.enum';
import { MediaItemMenuWithDeletion } from '../../../../../shared/components/media-item-menu-with-deletion/media-item-menu-with-deletion.component';
import { downloadMediaItem } from '../../../../../shared/media-utils';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { useMedia } from '../../../../media/providers/media-provider.component';
import { useSelectedDataset } from '../../project-dataset/use-selected-dataset/use-selected-dataset.hook';

interface MediaItemMenuProps {
    mediaItem: MediaItem;
    showQuickAnnotation: boolean;
    isAnomalyVideo: boolean;
    selectedMediaItemAction: Key | undefined;
    onChangeSelectedMediaItemAction: (key: Key | undefined) => void;
}

export const MediaItemMenu = ({
    mediaItem,
    showQuickAnnotation,
    isAnomalyVideo,
    selectedMediaItemAction,
    onChangeSelectedMediaItemAction,
}: MediaItemMenuProps): JSX.Element => {
    const selectedDataset = useSelectedDataset();
    const { deleteMedia, loadNextMedia } = useMedia();
    const datasetIdentifier = useDatasetIdentifier();
    const navigate = useNavigateToAnnotatorRoute(datasetIdentifier);

    const commonMenuItems = [MediaItemMenuActions.DELETE, MediaItemMenuActions.ANNOTATE, MediaItemMenuActions.DOWNLOAD];
    const items = showQuickAnnotation ? [...commonMenuItems, MediaItemMenuActions.QUICK_ANNOTATION] : commonMenuItems;

    const handleDelete = () => {
        deleteMedia.mutate([mediaItem], {
            onSuccess: async () => {
                !isAnomalyVideo && (await loadNextMedia(true));
            },
        });
    };

    return (
        <MediaItemMenuWithDeletion
            menuProps={{
                items,
                id: 'More',
                isQuiet: true,
                onAction: (action) => {
                    if (action === MediaItemMenuActions.ANNOTATE.toLowerCase()) {
                        navigate({ ...datasetIdentifier, mediaItem, active: selectedDataset.useForTraining });
                        return;
                    }

                    if (action === MediaItemMenuActions.DOWNLOAD.toLowerCase()) {
                        downloadMediaItem(mediaItem);
                        return;
                    }

                    onChangeSelectedMediaItemAction(action);
                },
            }}
            mediaItemName={mediaItem.name}
            isAnomalyVideo={isAnomalyVideo}
            handleDismiss={() => onChangeSelectedMediaItemAction(undefined)}
            handleDelete={handleDelete}
            dialogKey={selectedMediaItemAction}
        />
    );
};
