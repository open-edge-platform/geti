// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, Key, ReactNode } from 'react';

import { AlertDialog, DialogContainer, View } from '@geti/ui';

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
