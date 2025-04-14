// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import negate from 'lodash/negate';
import { v4 as uuid } from 'uuid';

import { Annotation, AnnotationLabel } from '../../core/annotations/annotation.interface';
import { Explanation } from '../../core/annotations/prediction.interface';
import { Point, Shape } from '../../core/annotations/shapes.interface';
import { isPrediction } from '../../core/labels/utils';
import { MediaItem } from '../../core/media/media.interface';
import { isVideo, isVideoFrame } from '../../core/media/video.interface';
import { DOMAIN } from '../../core/projects/core.interface';
import { hasEqualId } from '../../shared/utils';

export const hasEmptyLabels = (annotation: Annotation) => isEmpty(annotation.labels);
export const hasValidLabels = negate(hasEmptyLabels);
export const hasInvalidAnnotations = (annotations: ReadonlyArray<Annotation> = []) => annotations.some(hasEmptyLabels);

export const createAnnotation = (shape: Shape, labels: readonly AnnotationLabel[]): Annotation => {
    return {
        id: uuid(),
        labels,
        shape,
        isHidden: false,
        isLocked: false,
        isSelected: false,
        zIndex: 0,
    };
};

export const getLabeledShape = (
    id: string,
    shape: Shape,
    labels: AnnotationLabel[],
    isSelected = true,
    zIndex: number
): Annotation => ({
    id,
    labels,
    shape,
    zIndex,
    isSelected,
    isHidden: false,
    isLocked: false,
});

export const areAnnotationsIdentical = (
    annotations1: ReadonlyArray<Annotation> | Annotation[] | undefined = [],
    annotations2: ReadonlyArray<Annotation> | Annotation[] | undefined = []
): boolean => {
    // We don't care if the user has selected, hovered, hidden or locked the annotation
    const withoutInteractions = ({ id, shape, labels, zIndex }: Annotation) => {
        const labelsWithoutInteractions = labels.map((label) => ({
            id: label.id,
            // We don't consider labels with different scores as identical,
            // this is to make sure we display user and predicted labels differently
            score: label.score,
        }));
        return { id, shape, labels: labelsWithoutInteractions, zIndex };
    };

    return isEqual(annotations1.map(withoutInteractions), annotations2.map(withoutInteractions));
};

export const areLabelsIdentical = (
    labels1: readonly AnnotationLabel[] | AnnotationLabel[],
    labels2: readonly AnnotationLabel[] | AnnotationLabel[]
): boolean => {
    // We don't care about the color and hotkey of the label
    const withoutInteraction = ({ color: _color, hotkey: _hotkey, ...rest }: AnnotationLabel) => ({ ...rest });

    return isEqual(labels1.map(withoutInteraction), labels2.map(withoutInteraction));
};

export const getPercentage = (value: number): string => {
    return `${value + 100}%`;
};

// Helper that can be used by implementations of FindMediaItemCriteria that are based on
// the selected media item's index in the dataset
export const findIndex = (selectedMediaItem: MediaItem | undefined, mediaItems: MediaItem[]): number => {
    const idx = mediaItems.findIndex((mediaItem) => isEqual(mediaItem.identifier, selectedMediaItem?.identifier));

    if (idx === -1 && selectedMediaItem !== undefined && isVideoFrame(selectedMediaItem)) {
        const videoIdx = mediaItems.findIndex(
            (mediaItem) => isVideo(mediaItem) && mediaItem.identifier.videoId === selectedMediaItem.identifier.videoId
        );

        return videoIdx;
    }

    return idx;
};

export const filterHidden = ({ isHidden }: Annotation) => !isHidden;

export const filterForSelectedTask = (domain?: DOMAIN) => {
    return (annotation: Annotation) => {
        const { isSelected } = annotation;

        if (domain === DOMAIN.CLASSIFICATION) {
            return isSelected;
        }

        return true;
    };
};

export const getFormattedPoints = (points: Point[]): string => points.map(({ x, y }) => `${x},${y}`).join(' ');

export const isUserAnnotation = negate(isPrediction);

export const isPredictionAnnotation = (annotation: Annotation) => annotation.labels.some(isPrediction);

export const getPredictionAnnotations = (annotations: Annotation[] | ReadonlyArray<Annotation>) =>
    annotations.filter(isPredictionAnnotation);

export const filterForExplanation = (explanation: Explanation | undefined, explanationEnabled: boolean) => {
    if (!explanationEnabled || explanation === undefined || explanation.labelsId === '') {
        return () => true;
    }

    return (annotation: Annotation) => annotation.labels.find(hasEqualId(explanation.labelsId));
};

export const filterIfInEditMode = (isInEditMode: boolean) => {
    if (isInEditMode) {
        return ({ isSelected, isLocked }: Annotation) => !isSelected || (isSelected && isLocked);
    } else {
        return () => true;
    }
};
