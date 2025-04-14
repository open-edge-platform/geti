// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog, DialogContainer } from '@adobe/react-spectrum';
import { MutationStatus } from '@tanstack/react-query';

import { UseSubmitAnnotationsMutationResult } from '../../providers/submit-annotations-provider/submit-annotations.interface';

import classes from './invalid-annotations-dialog.module.scss';

interface SaveAnnotationsDialogProps {
    cancel: () => void;
    submitAnnotationsMutation: UseSubmitAnnotationsMutationResult;
    saveOnlyValidAnnotations: () => Promise<void>;
}

const doNothing = () => {
    // spectrum calls dismiss after a cancel or primary action, both of these actions
    // are assumed to close the dialog so we don't want to dismiss it as well
};

const InvalidAnnotationsDialogBody = ({ status }: { status: MutationStatus }) => {
    return (
        <>
            There are annotations without labels. Please make sure that all objects have labels.
            {status === 'error' ? (
                <>
                    <br />
                    <span className={classes.savingError}>Could not save annotations due to a server issue.</span>
                </>
            ) : (
                <></>
            )}
        </>
    );
};

const getPrimaryActionLabel = (status: MutationStatus) => {
    switch (status) {
        case 'pending':
            return 'Saving annotations...';
        case 'error':
            return 'Try again';
        case 'success':
        case 'idle':
            return 'Delete & continue';
    }
};

export const InvalidAnnotationsDialog = ({
    cancel,
    submitAnnotationsMutation,
    saveOnlyValidAnnotations,
}: SaveAnnotationsDialogProps): JSX.Element => {
    return (
        <DialogContainer onDismiss={doNothing} isDismissable={false}>
            <AlertDialog
                variant={submitAnnotationsMutation.status === 'error' ? 'error' : 'destructive'}
                title='Invalid annotations'
                primaryActionLabel={getPrimaryActionLabel(submitAnnotationsMutation.status)}
                cancelLabel='Cancel'
                onPrimaryAction={saveOnlyValidAnnotations}
                onCancel={cancel}
                isPrimaryActionDisabled={submitAnnotationsMutation.isPending}
            >
                <InvalidAnnotationsDialogBody status={submitAnnotationsMutation.status} />
            </AlertDialog>
        </DialogContainer>
    );
};
