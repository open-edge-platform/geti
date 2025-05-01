// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, Key } from 'react';

import { MediaItemMenuActions } from '@shared/components/media-item-menu-with-deletion/media-item-menu-actions.enum';
import { MediaItemMenuWithDeletion } from '@shared/components/media-item-menu-with-deletion/media-item-menu-with-deletion.component';
import { downloadMediaItem } from '@shared/media-utils';

import { MediaItem } from '../../../../../core/media/media.interface';
import { useDeleteDatasetItem } from './use-delete-dataset-item.hook';

const ITEMS = [MediaItemMenuActions.DELETE, MediaItemMenuActions.DOWNLOAD];

interface DeleteDatasetItemProps {
    mediaItem: MediaItem;
    isSelected: boolean;
    menuProps?: Partial<ComponentProps<typeof MediaItemMenuWithDeletion>['menuProps']>;
}

export const DatasetItemMenu = ({ mediaItem, isSelected, menuProps }: DeleteDatasetItemProps): JSX.Element => {
    const { dialogKey, setDialogKey, handleDelete, isAnomalyVideo } = useDeleteDatasetItem({ mediaItem, isSelected });

    const onAction = (key: Key) => {
        if (key === MediaItemMenuActions.DOWNLOAD.toLowerCase()) {
            downloadMediaItem(mediaItem);
        } else {
            setDialogKey(key);
        }
    };

    return (
        <MediaItemMenuWithDeletion
            menuProps={{
                id: 'media-item-menu-id',
                items: ITEMS,
                isQuiet: true,
                onAction,
                ...menuProps,
            }}
            mediaItemName={mediaItem.name}
            isAnomalyVideo={isAnomalyVideo}
            handleDismiss={() => setDialogKey(undefined)}
            handleDelete={handleDelete}
            dialogKey={dialogKey}
        />
    );
};
