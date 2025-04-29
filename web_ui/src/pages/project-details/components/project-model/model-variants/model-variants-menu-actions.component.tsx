// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
