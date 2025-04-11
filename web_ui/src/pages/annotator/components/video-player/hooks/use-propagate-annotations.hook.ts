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

import { useMemo } from 'react';

import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { AxiosError, isAxiosError } from 'axios';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import negate from 'lodash/negate';
import { v4 as uuidv4 } from 'uuid';

import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { hasEqualId } from '../../../../../shared/utils';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { useDatasetIdentifier } from '../../../hooks/use-dataset-identifier.hook';
import { useAnnotationScene } from '../../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useIsPredictionRejected } from '../../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { useSaveAnnotations } from '../../../providers/annotator-provider/use-save-annotations.hook';
import { useMergeAnnotations } from '../../../providers/prediction-provider/use-merge-annotations.hook';
import { useAnnotationsQuery } from '../../../providers/selected-media-item-provider/use-annotations-query.hook';
import { useSubmitAnnotations } from '../../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { hasInvalidAnnotations } from '../../../utils';
import { useVideoPlayer } from '../video-player-provider.component';
import { useConstructVideoFrame } from './use-construct-video-frame.hook';

interface UsePropagateAnnotations {
    isDisabled: boolean;
    showReplaceOrMergeDialog: boolean;
    propagateAnnotationsMutation: UseMutationResult<void, unknown, boolean, unknown>;
}

export const usePropagateAnnotations = (): UsePropagateAnnotations => {
    const isPredictionRejected = useIsPredictionRejected();
    const { videoControls, step, videoFrame: currentVideoFrame } = useVideoPlayer();

    const { annotations: replaceWithAnnotations } = useAnnotationScene();
    const acceptedAnnotations = replaceWithAnnotations.filter(negate(isPredictionRejected));

    const { selectedTask } = useTask();
    const { isTaskChainProject } = useProject();
    const { addNotification } = useNotification();

    const disableDueToTaskChain = isTaskChainProject && selectedTask !== null;

    const constructVideoFrame = useConstructVideoFrame(currentVideoFrame);

    const nextVideoFrame = useMemo(() => {
        if (videoControls.isPlaying) {
            return undefined;
        }

        if (!videoControls.canSelectNext) {
            return undefined;
        }

        return constructVideoFrame(currentVideoFrame.identifier.frameNumber + step);
    }, [
        constructVideoFrame,
        videoControls.isPlaying,
        step,
        videoControls.canSelectNext,
        currentVideoFrame.identifier.frameNumber,
    ]);

    // TODO: this can change if the user changes the selected dataset, which will
    // introduce a bug
    const datasetIdentifier = useDatasetIdentifier();
    const { annotationService } = useApplicationServices();
    const { project } = useProject();

    const annotationsInNextFrameQuery = useAnnotationsQuery({
        annotationService,
        coreLabels: project.labels,
        datasetIdentifier,
        mediaItem: nextVideoFrame,
        enabled: !videoControls.isPlaying,
    });

    const isDisabled =
        videoControls.isPlaying ||
        !videoControls.canSelectNext ||
        disableDueToTaskChain ||
        isEmpty(replaceWithAnnotations) ||
        !annotationsInNextFrameQuery.data ||
        hasInvalidAnnotations(replaceWithAnnotations);

    const showReplaceOrMergeDialog =
        annotationsInNextFrameQuery.isPending ||
        (annotationsInNextFrameQuery.isSuccess && annotationsInNextFrameQuery.data.length !== 0);

    const mergeAnnotations = useMergeAnnotations();

    const { submitAnnotationsMutation } = useSubmitAnnotations();
    // TODO: figure out if we can combine this with submitAnnotationsMutation
    const saveAnnotations = useSaveAnnotations();

    const propagateAnnotationsMutation = useMutation({
        mutationFn: async (merge: boolean) => {
            if (!nextVideoFrame) {
                return;
            }

            if (merge) {
                if (!annotationsInNextFrameQuery.isSuccess) {
                    // for development purposes
                    throw new Error('Could not retrieve annotations to merge with');
                }

                // We want to prevent overwriting the user's existing annotations, therefore all
                // annotations from the previous frame are given a new id if they were changed
                const annotationsWithNewIds = replaceWithAnnotations.map((annotation) => {
                    const isNewAnnotation = !annotationsInNextFrameQuery.data.some(hasEqualId(annotation.id));

                    if (isNewAnnotation) {
                        return annotation;
                    }

                    const annotationDidNotChange = annotationsInNextFrameQuery.data.some((otherAnnotation) =>
                        isEqual(otherAnnotation, annotation)
                    );

                    if (annotationDidNotChange) {
                        return annotation;
                    }

                    return { ...annotation, id: uuidv4() };
                });

                const mergedAnnotations = mergeAnnotations(annotationsWithNewIds, annotationsInNextFrameQuery.data);

                submitAnnotationsMutation.mutate({
                    annotations: acceptedAnnotations,
                    callback: async () => {
                        try {
                            await saveAnnotations(mergedAnnotations, nextVideoFrame);

                            videoControls.goto(nextVideoFrame.identifier.frameNumber);
                        } catch (error: unknown) {
                            if (isAxiosError(error)) {
                                addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                            }
                        }
                    },
                });
            } else {
                submitAnnotationsMutation.mutate({
                    annotations: acceptedAnnotations,
                    callback: async () => {
                        try {
                            await saveAnnotations(replaceWithAnnotations, nextVideoFrame);

                            videoControls.goto(nextVideoFrame.identifier.frameNumber);
                        } catch (error: unknown) {
                            if (isAxiosError(error)) {
                                addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                            }
                        }
                    },
                });
            }
        },

        onError: (error: AxiosError) => {
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    return {
        isDisabled,
        showReplaceOrMergeDialog,
        propagateAnnotationsMutation,
    };
};
