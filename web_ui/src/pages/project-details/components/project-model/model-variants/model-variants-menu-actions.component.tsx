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

import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { MenuTriggerList } from '../../../../../shared/components/menu-trigger-list/menu-trigger-list.component';
import { downloadFile, getDownloadNotificationMessage, isNonEmptyString } from '../../../../../shared/utils';
import { DownloadCell } from './download-cell/download-cell.component';

interface ModelVariantsMenuActionsProps {
    modelId: string;
    downloadUrl?: string;
    handleOpenRunTest: () => void;
}

export const ModelVariantsMenuActions = ({
    modelId,
    downloadUrl,
    handleOpenRunTest,
}: ModelVariantsMenuActionsProps): JSX.Element => {
    const { router } = useApplicationServices();
    const { addNotification } = useNotification();

    const downloadHandler = () => {
        if (!isNonEmptyString(downloadUrl)) {
            return;
        }

        downloadFile(router.PREFIX(downloadUrl));
        addNotification({ message: getDownloadNotificationMessage('model'), type: NOTIFICATION_TYPE.INFO });
    };

    const menuOptions: [string, () => void][] = [
        ['Run tests', handleOpenRunTest],
        ['Download', downloadHandler],
    ];

    return (
        <>
            <DownloadCell id={modelId} onDownload={downloadHandler} aria-label={'download model'} />
            <MenuTriggerList
                id={`optimized-model-action-menu-${modelId}`}
                options={menuOptions}
                ariaLabel={'Model action menu'}
            />
        </>
    );
};
