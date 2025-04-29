// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog, DialogContainer } from '@adobe/react-spectrum';

import { UseSubmitAnnotationsMutationResult } from '../../providers/submit-annotations-provider/submit-annotations.interface';

import classes from './invalid-annotations-dialog.module.scss';

interface SavingFailedDialogProps {
    cancel: () => void;
    retry: () => void;
    submitAnnotationsMutation: UseSubmitAnnotationsMutationResult;
}

const doNothing = () => {
    // spectrum calls dismiss after a cancel or primary action, both of these actions
    // are assumed to close the dialog so we don't want to dismiss it as well
};

export const SavingFailedDialog = ({
    submitAnnotationsMutation,
    cancel,
    retry,
}: SavingFailedDialogProps): JSX.Element => {
    if (submitAnnotationsMutation.error === null) {
        return <></>;
    }

    return (
        <DialogContainer onDismiss={doNothing} isDismissable={false}>
            <AlertDialog
                variant='error'
                title='Saving annotations'
                primaryActionLabel={submitAnnotationsMutation.isPending ? 'Saving annotations...' : 'Try again'}
                cancelLabel='Cancel'
                onPrimaryAction={retry}
                onCancel={cancel}
                isPrimaryActionDisabled={submitAnnotationsMutation.isPending}
            >
                Could not save annotations due to a server issue.
                <br />
                <span className={classes.savingError}>{submitAnnotationsMutation.error.message}</span>
            </AlertDialog>
        </DialogContainer>
    );
};
