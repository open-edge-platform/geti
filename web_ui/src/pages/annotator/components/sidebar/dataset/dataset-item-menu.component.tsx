// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps, Key } from 'react';

import { MediaItem } from '../../../../../core/media/media.interface';
import { MediaItemMenuActions } from '../../../../../shared/components/media-item-menu-with-deletion/media-item-menu-actions.enum';
import { MediaItemMenuWithDeletion } from '../../../../../shared/components/media-item-menu-with-deletion/media-item-menu-with-deletion.component';
import { downloadMediaItem } from '../../../../../shared/media-utils';
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
