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

import { Flex, View } from '@adobe/react-spectrum';
import { Virtuoso } from 'react-virtuoso';

import { MediaUploadItemState } from '../../../../../../providers/media-upload-provider/media-upload.interface';
import { useDatasetMediaUpload } from '../../../project-dataset/hooks/dataset-media-upload';
import { UploadStatusDialogItem, UploadStatusDialogItemTypes } from './upload-status-dialog-item.component';

const typeToType = {
    [MediaUploadItemState.ERROR]: UploadStatusDialogItemTypes.ERROR,
    [MediaUploadItemState.PROGRESS]: UploadStatusDialogItemTypes.PROGRESS,
    [MediaUploadItemState.QUEUED]: UploadStatusDialogItemTypes.COMMON,
    [MediaUploadItemState.SUCCESS]: UploadStatusDialogItemTypes.SUCCESS,
};

export const UploadStatusDialogContent = (): JSX.Element => {
    const { mediaUploadState } = useDatasetMediaUpload();
    const { list } = mediaUploadState;

    return (
        <View backgroundColor='gray-50' position='relative' padding={'size-150'}>
            <Flex direction='column' height={'size-3600'} UNSAFE_style={{ overflowY: 'scroll' }} gap={'size-100'}>
                <Virtuoso
                    totalCount={list.length}
                    itemContent={(index) => {
                        const currentItem = list.at(index);

                        if (currentItem === undefined) {
                            return null;
                        }

                        return <UploadStatusDialogItem item={currentItem} type={typeToType[currentItem.type]} />;
                    }}
                />
            </Flex>
        </View>
    );
};
