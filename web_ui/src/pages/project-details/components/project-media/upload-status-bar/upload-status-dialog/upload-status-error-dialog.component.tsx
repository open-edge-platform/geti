// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
