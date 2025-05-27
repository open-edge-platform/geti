// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { useNavigateToAnnotatorRoute } from '@geti/core/src/services/use-navigate-to-annotator-route.hook';

import { MediaItem } from '../../../../../core/media/media.interface';
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
    const navigate = useNavigateToAnnotatorRoute();

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
                        navigate({ datasetIdentifier, mediaItem, active: selectedDataset.useForTraining });
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
