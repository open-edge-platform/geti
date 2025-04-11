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

import { useState } from 'react';

import { View } from '@adobe/react-spectrum';

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
