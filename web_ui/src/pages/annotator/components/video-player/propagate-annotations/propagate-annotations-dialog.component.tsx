// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
