// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useRef, useState } from 'react';

import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { SubmitDialog } from '../../annotation/annotation-filter/submit-dialog.component';
import {
    SubmitAnnotationsContext,
    useSubmitAnnotations,
} from '../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { SaveAnnotationMutation } from '../../providers/submit-annotations-provider/submit-annotations.interface';
import { useAnnotationFilters } from './use-annotation-filters.hook';

export const AskToResetFilterBeforeSubmittingAnnotations = ({ children }: { children: ReactNode }) => {
    const submitAnnotations = useSubmitAnnotations();
    const [showDialog, setShowDialog] = useState(false);
    const submitMutationArguments = useRef<{
        callback?: () => Promise<void>;
        annotations: ReadonlyArray<Annotation>;
    }>();
    const [filters, setFilters] = useAnnotationFilters();

    const submitAnnotationsMutation: ReturnType<typeof useSubmitAnnotations>['submitAnnotationsMutation'] = useMutation<
        void,
        AxiosError,
        SaveAnnotationMutation
    >({
        mutationFn: async ({ annotations, callback }) => {
            const shouldAskTheUserToResetFilters = filters.length > 0;

            if (shouldAskTheUserToResetFilters) {
                setShowDialog(true);
                submitMutationArguments.current = { annotations, callback };
            } else {
                await submitAnnotations.submitAnnotationsMutation.mutateAsync({
                    annotations,
                    callback,
                });
            }
        },
    });

    const value = { ...submitAnnotations, submitAnnotationsMutation };

    return (
        <SubmitAnnotationsContext.Provider value={value}>
            {children}
            {showDialog && (
                <SubmitDialog
                    onCancel={async (): Promise<void> => {
                        submitMutationArguments.current = undefined;
                        setShowDialog(false);
                    }}
                    onSubmit={async (): Promise<void> => {
                        setShowDialog(false);
                        if (submitMutationArguments.current !== undefined) {
                            submitAnnotations.submitAnnotationsMutation.mutate(submitMutationArguments.current);
                        }
                    }}
                    onClearFilter={async (): Promise<void> => {
                        setShowDialog(false);
                        setFilters([]);
                    }}
                />
            )}
        </SubmitAnnotationsContext.Provider>
    );
};
