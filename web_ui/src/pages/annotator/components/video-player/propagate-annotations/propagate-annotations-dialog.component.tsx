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

import { ButtonGroup, Content, Dialog, Divider, Text } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import { UseMutationResult } from '@tanstack/react-query';

import { Button } from '../../../../../shared/components/button/button.component';

interface PropagateAnnotationsDialogProps {
    propagateAnnotationsMutation: UseMutationResult<void, unknown, boolean, unknown>;
    close: () => void;
}

export const PropagateAnnotationsDialog = ({
    propagateAnnotationsMutation,
    close,
}: PropagateAnnotationsDialogProps): JSX.Element => {
    const isDisabled = propagateAnnotationsMutation.isPending;

    const onReplace = () => {
        propagateAnnotationsMutation.mutate(false, { onSettled: close });
    };

    const onMerge = () => {
        propagateAnnotationsMutation.mutate(true, { onSettled: close });
    };

    return (
        <Dialog>
            <Heading>Replace or merge annotations?</Heading>
            <Divider />
            <Content>
                <Text>
                    Do you want to replace your annotations the annotations from this frame or merge them as new ones?
                </Text>
            </Content>
            <ButtonGroup>
                <Button
                    variant='primary'
                    onPress={close}
                    id='video-player-cancel-propagate-annotations'
                    isDisabled={isDisabled}
                >
                    Cancel
                </Button>
                <Button
                    variant='primary'
                    onPress={onMerge}
                    id='video-player-merge-propagate-annotations'
                    isDisabled={isDisabled}
                >
                    Merge
                </Button>
                <Button
                    variant='primary'
                    onPress={onReplace}
                    id='video-player-replace-propagate-annotations'
                    isDisabled={isDisabled}
                >
                    Replace
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
