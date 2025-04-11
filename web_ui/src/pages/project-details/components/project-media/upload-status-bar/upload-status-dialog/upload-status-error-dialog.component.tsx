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

import { Content, Dialog, Divider, Heading, View } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import { ErrorListItem } from '../../../../../../providers/media-upload-provider/media-upload.interface';

interface UploadStatusErrorDialogProps {
    item: ErrorListItem;
}

export const UploadStatusErrorDialog = ({ item }: UploadStatusErrorDialogProps): JSX.Element => {
    const getErrorText = (errorItem: ErrorListItem): JSX.Element => {
        if (errorItem.errors && errorItem.errors.length > 0)
            return (
                <>
                    {errorItem.errors.map((error: string, index: number) => (
                        <View key={`upload-error-${index}`}>{error}</View>
                    ))}
                </>
            );

        return <Text>Something went wrong. Please try again later.</Text>;
    };

    return (
        <Dialog isDismissable size='M'>
            <Heading>{`ERROR ${item.status && item.status > 0 ? item.status : ''} ${item.statusText ?? ''}`}</Heading>
            <Divider />
            <Content>{getErrorText(item)}</Content>
        </Dialog>
    );
};
