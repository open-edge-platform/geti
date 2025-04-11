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

import { ButtonGroup, Flex, Heading, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isString from 'lodash/isString';

import { ExportDatasetLSData } from '../../../../../core/projects/dataset.interface';
import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { Button } from '../../../../../shared/components/button/button.component';
import { downloadFile, getDownloadNotificationMessage, getFileSize } from '../../../../../shared/utils';

import classes from '../project-dataset.module.scss';

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
