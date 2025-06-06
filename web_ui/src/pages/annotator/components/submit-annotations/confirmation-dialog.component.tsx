// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading, Loading } from '@geti/ui';
import { MutationStatus } from '@tanstack/react-query';

import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { UseSubmitAnnotationsMutationResult } from '../../providers/submit-annotations-provider/submit-annotations.interface';

import classes from './invalid-annotations-dialog.module.scss';

interface ConfirmationDialogProps {
    onCancel: () => Promise<void>;
    onSubmit: () => Promise<void>;
    onDiscard: () => Promise<void>;
    submitAnnotationsMutation: UseSubmitAnnotationsMutationResult;
}

const SubmitButtonBody = ({ status }: { status: MutationStatus }) => {
    switch (status) {
        case 'pending':
            return (
                <>
                    <Loading mode='inline' size='S' marginEnd='size-100' />
                    Submit
                </>
            );
        case 'error':
            return <>Try again</>;
        case 'success':
        case 'idle':
            return <>Submit</>;
    }
};

export const ConfirmationDialog = ({
    onCancel,
    onSubmit,
    onDiscard,
    submitAnnotationsMutation,
}: ConfirmationDialogProps): JSX.Element => {
    const { selectedMediaItemQuery } = useSelectedMediaItem();
    const isDisabled = submitAnnotationsMutation.isPending || selectedMediaItemQuery.isPending;

    return (
        <DialogContainer onDismiss={onCancel} isDismissable={false}>
            <Dialog size='M'>
                <Heading>Discard or submit annotations</Heading>
                <Divider />
                <Content>
                    Annotations in this image are not submitted. Discard or submit annotations.
                    {submitAnnotationsMutation.error !== null ? (
                        <>
                            <br />
                            <span className={classes.savingError}>{submitAnnotationsMutation.error?.message}</span>
                        </>
                    ) : (
                        <></>
                    )}
                </Content>

                <ButtonGroup>
                    <Button
                        variant='secondary'
                        onPress={onCancel}
                        isDisabled={isDisabled}
                        id='cancel-saving-confirmation'
                    >
                        Cancel
                    </Button>
                    <Button
                        variant='negative'
                        onPress={onDiscard}
                        isDisabled={isDisabled}
                        id='discard-saving-confirmation'
                    >
                        Discard
                    </Button>
                    <Button variant='accent' onPress={onSubmit} isDisabled={isDisabled} id='submit-saving-confirmation'>
                        <SubmitButtonBody status={submitAnnotationsMutation.status} />
                    </Button>
                </ButtonGroup>
            </Dialog>
        </DialogContainer>
    );
};
