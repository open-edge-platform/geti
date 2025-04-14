// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
