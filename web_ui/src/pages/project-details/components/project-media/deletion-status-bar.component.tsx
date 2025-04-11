// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
