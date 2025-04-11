// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useApplicationServices } from '../../core/services/application-services-provider.component';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { downloadFile, getDownloadNotificationMessage } from '../../shared/utils';
import { DownloadButton } from './download-button.component';

interface DownloadServerInfoProps {
    url: string;
    exportName: string;
}

export const DownloadServerInfo = ({ exportName, url }: DownloadServerInfoProps): JSX.Element => {
    const { router } = useApplicationServices();
    const { addNotification } = useNotification();

    const handlePress = () => {
        downloadFile(router.PREFIX(url));

        addNotification({ message: getDownloadNotificationMessage(exportName), type: NOTIFICATION_TYPE.INFO });
    };

    return <DownloadButton exportName={exportName} handlePress={handlePress} />;
};
