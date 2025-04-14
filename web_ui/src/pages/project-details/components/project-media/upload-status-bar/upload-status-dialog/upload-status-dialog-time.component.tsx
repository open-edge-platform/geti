// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Text, View } from '@adobe/react-spectrum';

import { getElapsedTimeText } from '../../../../../../providers/media-upload-provider/utils';
import { useDatasetMediaUpload } from '../../../project-dataset/hooks/dataset-media-upload';

export const UploadStatusDialogTime = (): JSX.Element => {
    const {
        mediaUploadState: { timeUploadStarted },
    } = useDatasetMediaUpload();

    return (
        <View right={0} position='absolute' bottom='size-1200' width='100%'>
            <View marginX='size-500' paddingTop='size-50' paddingBottom='size-100' marginEnd={45}>
                <Divider size='S' />
                <Flex alignItems='center' justifyContent='end'>
                    <View paddingTop='size-50' paddingEnd='size-100'>
                        <Text>{getElapsedTimeText(timeUploadStarted)}</Text>
                    </View>
                </Flex>
            </View>
        </View>
    );
};
