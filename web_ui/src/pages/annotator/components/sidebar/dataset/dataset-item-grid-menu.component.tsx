// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { View } from '@geti/ui';

import { MediaItem } from '../../../../../core/media/media.interface';
import { DatasetItemMenu } from './dataset-item-menu.component';

import classes from './dataset-accordion.module.scss';

interface DatasetItemDetailsMenuProps {
    mediaItem: MediaItem;
    isSelected: boolean;
}

export const DatasetItemGridMenu = ({ mediaItem, isSelected }: DatasetItemDetailsMenuProps): JSX.Element => {
    const [isMenuOpened, setIsMenuOpened] = useState<boolean>(false);

    return (
        <View
            position={'absolute'}
            top={'size-50'}
            right={'size-50'}
            backgroundColor={'gray-100'}
            borderRadius={'regular'}
            overflow={'hidden'}
            height={'size-400'}
            width={'size-400'}
            UNSAFE_className={isMenuOpened ? undefined : classes.datasetItemMenu}
            data-testid={'dataset-item-menu-id'}
            // in case of the video, we want this menu to be above player icon layer
            zIndex={10}
        >
            <DatasetItemMenu
                mediaItem={mediaItem}
                isSelected={isSelected}
                menuProps={{ onOpenChange: setIsMenuOpened }}
            />
        </View>
    );
};
