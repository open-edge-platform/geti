// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, View, VirtualizedListLayout } from '@geti/ui';

import {
    MediaUploadItem,
    MediaUploadItemState,
} from '../../../../../../providers/media-upload-provider/media-upload.interface';
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
                <VirtualizedListLayout
                    items={list}
                    idFormatter={(item) => `${item.uploadId}-${item.uploadId}`}
                    textValueFormatter={(item) => item.fileName}
                    layoutOptions={{ gap: 10 }}
                    renderItem={(item: MediaUploadItem) => (
                        <UploadStatusDialogItem item={item} type={typeToType[item.type]} />
                    )}
                />
            </Flex>
        </View>
    );
};
