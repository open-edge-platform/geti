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

import negate from 'lodash/negate';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { useIsPredictionRejected } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { UseSubmitAnnotationsMutationResult } from '../../providers/submit-annotations-provider/submit-annotations.interface';
import { hasInvalidAnnotations, hasValidLabels } from '../../utils';
import { ConfirmationDialog } from './confirmation-dialog.component';
import { InvalidAnnotationsDialog } from './invalid-annotations-dialog.component';
import { SavingFailedDialog } from './saving-failed-dialog.component';

interface SubmitDialogsProps {
    annotations: ReadonlyArray<Annotation>;
    cancel: () => Promise<void>;
    discard: () => Promise<void>;
    submit: (annotations: Annotation[]) => Promise<void>;
    showFailDialog: boolean;
    showConfirmationDialog: boolean;
    submitAnnotationsMutation: UseSubmitAnnotationsMutationResult;
}

export const SubmitDialogs = ({
    annotations,
    cancel,
    discard,
    submit,
    submitAnnotationsMutation,
    showConfirmationDialog,
    showFailDialog,
}: SubmitDialogsProps): JSX.Element => {
    const isPredictionRejected = useIsPredictionRejected();
    const acceptedAnnotations = annotations.filter(negate(isPredictionRejected));

    if (showFailDialog && hasInvalidAnnotations(acceptedAnnotations)) {
        return (
            <InvalidAnnotationsDialog
                cancel={cancel}
                submitAnnotationsMutation={submitAnnotationsMutation}
                saveOnlyValidAnnotations={async () => {
                    const validAnnotations = acceptedAnnotations.filter(hasValidLabels);

                    submitAnnotationsMutation.mutate({ annotations: validAnnotations });
                }}
            />
        );
    }

    if (showConfirmationDialog) {
        return (
            <ConfirmationDialog
                onCancel={cancel}
                onDiscard={discard}
                onSubmit={() => submit(acceptedAnnotations)}
                submitAnnotationsMutation={submitAnnotationsMutation}
            />
        );
    }

    if (submitAnnotationsMutation.isError) {
        return (
            <SavingFailedDialog
                submitAnnotationsMutation={submitAnnotationsMutation}
                cancel={cancel}
                retry={() => submitAnnotationsMutation.mutate({ annotations: acceptedAnnotations })}
            />
        );
    }

    return <></>;
};
