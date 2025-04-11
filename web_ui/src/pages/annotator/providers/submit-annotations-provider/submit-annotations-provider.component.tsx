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

import { createContext, ReactNode, useCallback, useContext, useMemo, useState } from 'react';

import isFunction from 'lodash/isFunction';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { SubmitDialogs } from '../../components/submit-annotations/submit-dialogs.component';
import { useAnalyticsAnnotationTools } from '../analytics-annotation-scene-provider/analytics-annotation-scene-provider.component';
import { SelectedMediaItem } from '../selected-media-item-provider/selected-media-item.interface';
import { UseSubmitAnnotationsMutationResult } from './submit-annotations.interface';
import { useSubmitAnnotationsMutation } from './use-submit-annotations-mutation.hook';
import { hasMediaPredictionChanges } from './utils';

type UnfinishedShapesCallback = (() => Annotation[]) | null;

export interface SubmitAnnotationsContextProps {
    setUnfinishedShapeCallback: (callback: UnfinishedShapesCallback) => void;
    submitAnnotationsMutation: UseSubmitAnnotationsMutationResult;
    confirmSaveAnnotations: (callback?: () => Promise<void>) => Promise<void>;
}

export const SubmitAnnotationsContext = createContext<SubmitAnnotationsContextProps | undefined>(undefined);
interface SubmitAnnotationsProviderProps {
    children: ReactNode;
    settings: UseSettings<UserProjectSettings>;
    annotations: ReadonlyArray<Annotation>;
    currentMediaItem: SelectedMediaItem | undefined;
    discardAnnotations: () => void;
    saveAnnotations: (annotations: ReadonlyArray<Annotation>) => Promise<void>;
}

// Allows the user to save their annotations and select another media item to annotate
// if saving is not possible due to an error or invalid annotations we show a dialog
// and allow the user to either try again or edit their annotations
export const SubmitAnnotationsProvider = ({
    children,
    settings,
    saveAnnotations,
    discardAnnotations,
    currentMediaItem: mediaItem,
    annotations: userAnnotations,
}: SubmitAnnotationsProviderProps): JSX.Element => {
    const [showFailDialog, setShowFailDialog] = useState(false);
    const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
    const { resetToolPerAnnotation } = useAnalyticsAnnotationTools();

    const settingsConfig = useMemo(() => getSettingsOfType(settings.config, FEATURES_KEYS), [settings.config]);
    const isInitialPredictionsEnabled = Boolean(settingsConfig[FEATURES_KEYS.INITIAL_PREDICTION].isEnabled);

    const { submitAnnotationsMutation, afterSaving, unfinishedShapesCallback, callCallbackAndClear } =
        useSubmitAnnotationsMutation(mediaItem, setShowFailDialog, setShowConfirmationDialog, saveAnnotations);

    const confirmSaveAnnotations = useCallback(
        async (callback?: () => Promise<void>) => {
            if (isFunction(callback)) {
                afterSaving.current = callback;
            }

            const predictions = isInitialPredictionsEnabled ? mediaItem?.predictions?.annotations : [];
            const newAnnotations = isFunction(unfinishedShapesCallback.current)
                ? unfinishedShapesCallback.current()
                : userAnnotations;

            const containsChanges = hasMediaPredictionChanges(mediaItem?.annotations, predictions, newAnnotations);

            if (containsChanges) {
                setShowConfirmationDialog(true);

                return;
            }

            callCallbackAndClear();
        },
        [
            mediaItem,
            afterSaving,
            userAnnotations,
            unfinishedShapesCallback,
            isInitialPredictionsEnabled,
            callCallbackAndClear,
        ]
    );

    // For the confirmation dialog
    const discard = useCallback(async () => {
        discardAnnotations();
        callCallbackAndClear();

        setShowConfirmationDialog(false);
        setShowFailDialog(false);

        resetToolPerAnnotation();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [callCallbackAndClear, discardAnnotations]);

    const submit = useCallback(
        async (newUserAnnotations: Annotation[]) => {
            const annotations = isFunction(unfinishedShapesCallback.current)
                ? unfinishedShapesCallback.current()
                : newUserAnnotations;

            submitAnnotationsMutation.mutate({ annotations });
        },
        [submitAnnotationsMutation, unfinishedShapesCallback]
    );

    const cancel = useCallback(async () => {
        afterSaving.current = undefined;
        submitAnnotationsMutation.reset();

        setShowConfirmationDialog(false);
        setShowFailDialog(false);
    }, [submitAnnotationsMutation, afterSaving]);

    const value = {
        setUnfinishedShapeCallback: (callback: UnfinishedShapesCallback) => {
            unfinishedShapesCallback.current = callback;
        },
        submitAnnotationsMutation,
        confirmSaveAnnotations,
    };

    return (
        <SubmitAnnotationsContext.Provider value={value}>
            {children}

            <SubmitDialogs
                cancel={cancel}
                submit={submit}
                discard={discard}
                annotations={userAnnotations}
                showFailDialog={showFailDialog}
                showConfirmationDialog={showConfirmationDialog}
                submitAnnotationsMutation={submitAnnotationsMutation}
            />
        </SubmitAnnotationsContext.Provider>
    );
};

export const useSubmitAnnotations = (): SubmitAnnotationsContextProps => {
    const context = useContext(SubmitAnnotationsContext);

    if (context === undefined) {
        throw new MissingProviderError('useSubmitAnnotations', 'SubmitAnnotationsProvider');
    }

    return context;
};
