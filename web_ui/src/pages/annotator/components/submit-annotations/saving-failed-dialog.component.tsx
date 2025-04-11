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
