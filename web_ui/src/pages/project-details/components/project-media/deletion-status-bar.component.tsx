// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';

interface DeletionStatusBarProps {
    visible: boolean;
}

export const DeletionStatusBar = ({ visible }: DeletionStatusBarProps): JSX.Element => {
    const { addNotification, removeNotification } = useNotification();
    const deletingMediasRef = useRef('');

    useEffect(() => {
        if (!visible) {
            removeNotification(deletingMediasRef.current);
        }

        if (visible) {
            deletingMediasRef.current = addNotification({
                hasCloseButton: false,
                message: 'Media deletion in progress...',
                type: NOTIFICATION_TYPE.DEFAULT,
                dismiss: { duration: 0 },
            });
        }
    }, [addNotification, removeNotification, visible]);

    return <></>;
};
