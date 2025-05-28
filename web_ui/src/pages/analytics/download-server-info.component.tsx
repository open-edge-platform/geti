// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';

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
