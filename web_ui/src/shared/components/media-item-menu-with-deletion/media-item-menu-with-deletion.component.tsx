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

import { ComponentProps, Key, ReactNode } from 'react';

import { AlertDialog, DialogContainer, View } from '@adobe/react-spectrum';

import { DELETE_ANOMALY_VIDEO_WARNING } from '../../../pages/project-details/components/project-media/media-item-tooltip-message/utils';
import { MenuTriggerButton } from '../menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { MediaItemMenuActions } from './media-item-menu-actions.enum';

interface MediaItemMenuWithDeletionProps {
    menuProps: ComponentProps<typeof MenuTriggerButton>;
    mediaItemName: string;
    isAnomalyVideo: boolean;
    handleDismiss: () => void;
    handleDelete: () => void;
    children?: ReactNode;
    dialogKey: Key | undefined;
}

export const MediaItemMenuWithDeletion = ({
    menuProps,
    handleDismiss,
    dialogKey,
    children,
    handleDelete,
    isAnomalyVideo,
    mediaItemName,
}: MediaItemMenuWithDeletionProps): JSX.Element => {
    const question = `Are you sure you want to delete "${mediaItemName}"?`;

    return (
        <>
            <MenuTriggerButton {...menuProps} />
            <DialogContainer onDismiss={handleDismiss}>
                {dialogKey === MediaItemMenuActions.DELETE.toLowerCase() && (
                    <AlertDialog
                        title='Delete'
                        variant='destructive'
                        primaryActionLabel='Delete'
                        onPrimaryAction={handleDelete}
                        cancelLabel={'Cancel'}
                        UNSAFE_style={{ wordBreak: 'break-word' }}
                    >
                        {question}
                        {isAnomalyVideo && <View marginTop={'size-75'}>{DELETE_ANOMALY_VIDEO_WARNING}</View>}
                    </AlertDialog>
                )}
                {children}
            </DialogContainer>
        </>
    );
};
