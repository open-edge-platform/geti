// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, useEffect } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { Button, Loading } from '@geti/ui';
import { useQueryClient } from '@tanstack/react-query';
import { isEmpty, isFunction, isNil } from 'lodash-es';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { hasEqualSize } from '../../../../shared/utils';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useNextMediaItem } from '../../hooks/use-next-media-item.hook';
import { useSaveAnnotationsKeyboardShortcut } from '../../hot-keys/use-save-annotations-keyboard-shortcut/use-save-annotations-keyboard-shortcut';
import { useDataset } from '../../providers/dataset-provider/dataset-provider.component';
import { useSelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useSubmitAnnotations } from '../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { getPredictionAnnotations } from '../../utils';
import { findNextAnnotationCriteria, findNextCriteria, findNextVideoFrameCriteria } from '../utils';
import { useConstructVideoFrame } from '../video-player/hooks/use-construct-video-frame.hook';

interface SubmitButtonProps {
    canSubmit: boolean;
    isDisabled?: boolean;
    styles?: CSSProperties;
    onSubmitEnd?: () => void;
    newAnnotations: Annotation[];
    selectedMediaItem: MediaItem | undefined;
    annotationToolContext: AnnotationToolContext;
    selectMediaItem: (mediaItem: MediaItem) => void;
}

const isOnlyPredictions = (annotations: Annotation[]) => {
    const prediction = getPredictionAnnotations(annotations);

    return !isEmpty(prediction) && hasEqualSize(prediction, annotations);
};

const useForceUpdateLastMedia = (
    setSelectedMediaItem: (media: MediaItem) => void,
    selectedMediaItem?: MediaItem,
    taskId?: string
) => {
    const queryClient = useQueryClient();

    return async () => {
        if (!selectedMediaItem) {
            return;
        }

        // In general, this is handled by useOptimisticallyUpdateAnnotationStatus.
        // However, the last media item does not have 'next item', and the current
        // item is used to 'force' selectedMediaItemQuery to acknowledge the recently saved annotations.
        await queryClient.invalidateQueries({
            queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.ANNOTATIONS(selectedMediaItem.identifier, 'latest'),
        });

        queryClient.removeQueries({
            queryKey: QUERY_KEYS.SELECTED_MEDIA_ITEM.SELECTED(selectedMediaItem.identifier, taskId),
        });

        setSelectedMediaItem(selectedMediaItem);
    };
};

export const SubmitButton = ({
    styles,
    canSubmit,
    newAnnotations,
    isDisabled = false,
    selectedMediaItem,
    annotationToolContext,
    onSubmitEnd,
    selectMediaItem,
}: SubmitButtonProps): JSX.Element => {
    const queryClient = useQueryClient();
    const { datasetIdentifier } = useDataset();
    const { mediaItemsQuery } = useDataset();

    const { selectedTask } = useTask();

    const { submitAnnotationsMutation } = useSubmitAnnotations();

    const buttonText = isOnlyPredictions(newAnnotations) ? 'Accept' : 'Submit';

    const { selectedMediaItemQuery } = useSelectedMediaItem();

    const nextMediaItem = useNextMediaItem(
        selectedMediaItem,
        findNextCriteria,
        findNextVideoFrameCriteria,
        selectedTask === null || isClassificationDomain(selectedTask.domain)
            ? () => undefined
            : findNextAnnotationCriteria
    );

    const isLastMediaItem = nextMediaItem === undefined;
    const lastMediaCallback = useForceUpdateLastMedia(selectMediaItem, selectedMediaItem, selectedTask?.id);
    const constructVideoFrame = useConstructVideoFrame(selectedMediaItem);
    const mutationOptions = { onSettled: async () => isFunction(onSubmitEnd) && onSubmitEnd() };

    useEffect(() => {
        if (isLastMediaItem && !mediaItemsQuery.isFetchingNextPage && mediaItemsQuery.hasNextPage) {
            mediaItemsQuery.fetchNextPage();
        }
    }, [mediaItemsQuery, isLastMediaItem]);

    const onPress = () => {
        if (isLastMediaItem) {
            submitAnnotationsMutation.mutate(
                { annotations: newAnnotations, callback: lastMediaCallback },
                mutationOptions
            );

            return;
        }

        if (nextMediaItem.type === 'media') {
            const callback = async () => selectMediaItem(nextMediaItem.media);

            submitAnnotationsMutation.mutate({ annotations: newAnnotations, callback }, mutationOptions);
        }

        if (nextMediaItem.type === 'videoFrame') {
            const videoFrame = constructVideoFrame(nextMediaItem.frameNumber);

            if (videoFrame !== undefined) {
                const callback = async () => {
                    await queryClient.invalidateQueries({
                        queryKey: QUERY_KEYS.ADVANCED_MEDIA_FRAME_ITEMS(datasetIdentifier, {}, {}),
                    });
                    selectMediaItem(videoFrame);
                };

                submitAnnotationsMutation.mutate({ annotations: newAnnotations, callback }, mutationOptions);
            }
        }

        if (nextMediaItem.type === 'annotation') {
            // Selecting annotation with onSuccess resulted in a race condition
            submitAnnotationsMutation.mutateAsync({ annotations: newAnnotations }, mutationOptions).then(() => {
                annotationToolContext.scene.selectAnnotation(nextMediaItem.annotation.id);
            });
        }
    };

    const isLoadingOrBlock = submitAnnotationsMutation.isPending || (nextMediaItem === undefined && !canSubmit);
    const isSubmitDisabled = isDisabled || isLoadingOrBlock || selectedMediaItemQuery.isFetching;

    useSaveAnnotationsKeyboardShortcut(onPress, !isSubmitDisabled);

    return (
        <Button
            variant='accent'
            onPress={onPress}
            UNSAFE_style={styles}
            isDisabled={isSubmitDisabled}
            id='secondary-toolbar-submit'
            aria-label='Submit annotations'
        >
            {submitAnnotationsMutation.isPending ? <Loading mode='inline' size='S' marginEnd='size-100' /> : <></>}
            {buttonText} {!isNil(nextMediaItem) && '»'}
        </Button>
    );
};
