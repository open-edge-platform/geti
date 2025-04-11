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
