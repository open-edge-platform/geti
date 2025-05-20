// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { Button, ButtonGroup, Flex, Heading, Text, View } from '@geti/ui';
import { isEmpty, isString } from 'lodash-es';

import { ExportDatasetLSData } from '../../../core/projects/dataset.interface';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { downloadFile, getDownloadNotificationMessage, getFileSize } from '../../../shared/utils';

import classes from './dataset-export.module.scss';

interface ExportDatasetDownloadProps {
    onCloseDownload: (id: string) => void;
    localStorageData: ExportDatasetLSData;
}
export const ExportDatasetDownload = ({ onCloseDownload, localStorageData }: ExportDatasetDownloadProps) => {
    const { datasetId, downloadUrl, size, datasetName, exportFormat } = localStorageData;
    const { router } = useApplicationServices();
    const { addNotification } = useNotification();

    if (!isString(downloadUrl) || isEmpty(downloadUrl)) {
        return <></>;
    }

    const handleDownload = () => {
        downloadFile(router.PREFIX(downloadUrl), `intel_geti_${datasetId}.zip`);
        addNotification({ message: getDownloadNotificationMessage('dataset'), type: NOTIFICATION_TYPE.INFO });

        onCloseDownload(datasetId);
    };

    return (
        <div aria-label='export-dataset-download' className={classes.exportStatusContainer}>
            <View padding={'size-200'}>
                <Flex justifyContent={'space-between'} alignItems={'end'}>
                    <View>
                        <Heading level={6} UNSAFE_className={classes.exportStatusTitle}>
                            Dataset {`"${datasetName}"`} is ready to download.{' '}
                        </Heading>
                        <Text UNSAFE_style={{ display: 'block' }}>Format: {exportFormat.toLocaleUpperCase()}</Text>
                        {size ? <Text>Size: {`${getFileSize(size)}`}</Text> : null}
                    </View>
                    <ButtonGroup>
                        <Button variant='secondary' onPress={() => onCloseDownload(datasetId)}>
                            Close
                        </Button>
                        <Button variant='primary' onPress={handleDownload}>
                            Download
                        </Button>
                    </ButtonGroup>
                </Flex>
            </View>
        </div>
    );
};
