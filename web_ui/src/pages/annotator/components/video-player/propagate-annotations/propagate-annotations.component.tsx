// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DialogTrigger } from '@adobe/react-spectrum';

import { usePropagateAnnotations } from '../hooks/use-propagate-annotations.hook';
import { PropagateAnnotationsButton } from './propagate-annotations-button.component';
import { PropagateAnnotationsDialog } from './propagate-annotations-dialog.component';

export const PropagateAnnotations = (): JSX.Element => {
    const { isDisabled, propagateAnnotationsMutation, showReplaceOrMergeDialog } = usePropagateAnnotations();

    if (!showReplaceOrMergeDialog) {
        return (
            <PropagateAnnotationsButton
                isDisabled={isDisabled || propagateAnnotationsMutation.isPending}
                onPress={() => propagateAnnotationsMutation.mutate(false)}
            />
        );
    }

    return (
        <DialogTrigger>
            <PropagateAnnotationsButton isDisabled={isDisabled} />

            {(close) => (
                <PropagateAnnotationsDialog close={close} propagateAnnotationsMutation={propagateAnnotationsMutation} />
            )}
        </DialogTrigger>
    );
};
