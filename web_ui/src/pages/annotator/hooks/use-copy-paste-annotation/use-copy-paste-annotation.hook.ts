// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { useHotkeys } from 'react-hotkeys-hook';
import { useLocalStorage } from 'usehooks-ts';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getCenterOfShape } from '../../../../core/annotations/math';
import { labelFromUser } from '../../../../core/annotations/utils';
import { Label } from '../../../../core/labels/label.interface';
import { isPrediction } from '../../../../core/labels/utils';
import { MediaItem } from '../../../../core/media/media.interface';
import { isClassificationDomain, isKeypointDetection } from '../../../../core/projects/domains';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { LOCAL_STORAGE_KEYS } from '../../../../shared/local-storage-keys';
import { isNonEmptyArray } from '../../../../shared/utils';
import { getMediaId } from '../../../media/utils';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { HOTKEY_OPTIONS } from '../../hot-keys/utils';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { isShapePartiallyWithinROI, isShapeWithinRoi, removeOffLimitPoints } from '../../tools/geometry-utils';
import { translateAnnotation } from '../../tools/utils';
import { createAnnotation } from '../../utils';
import { useZoom } from '../../zoom/zoom-provider.component';
import { useAnnotatorHotkeys } from '../use-hotkeys-configuration.hook';
import { getTranslateVector, hasValidLabelsAndStructure } from './utils';

interface UseCopyPasteAnnotation {
    scene: AnnotationScene;
    taskLabels: Label[];
    image: ImageData;
    selectedMediaItem: MediaItem | undefined;
    hasMultipleAnnotations?: boolean;
    selectedAnnotations: Annotation[];
}

const OFFSET = 10;

export const useCopyPasteAnnotation = ({
    scene,
    image,
    taskLabels,
    selectedMediaItem,
    selectedAnnotations,
    hasMultipleAnnotations = false,
}: UseCopyPasteAnnotation) => {
    const { roi } = useROI();
    const { hotkeys } = useAnnotatorHotkeys();
    const { selectedTask } = useTask();
    const { addNotification } = useNotification();
    const { organizationId } = useOrganizationIdentifier();

    const {
        zoomState: { zoom },
    } = useZoom();

    const isNotClassificationTask = !(selectedTask && isClassificationDomain(selectedTask.domain));
    // Todo: This will be removed once support for multiple keypoint annotations is implemented
    const canHaveMultipleAnnotations = selectedTask?.domain && !isKeypointDetection(selectedTask.domain);

    const pasteCounter = useRef<number>(0);
    const mediaId = useRef<string>('');
    const { useActiveUser } = useUsers();
    const { data: activeUser } = useActiveUser(organizationId);

    const [lsAnnotations, setLsAnnotations] = useLocalStorage<Annotation[] | null>(
        LOCAL_STORAGE_KEYS.COPY_ANNOTATION,
        null
    );

    useHotkeys(
        `${hotkeys.undo}`,
        () => {
            if (pasteCounter.current > 0) {
                pasteCounter.current--;
            }
        },
        { ...HOTKEY_OPTIONS, enabled: isNotClassificationTask }
    );

    useHotkeys(
        `${hotkeys.redo}, ${hotkeys.redoSecond}`,
        () => {
            pasteCounter.current++;
        },
        { ...HOTKEY_OPTIONS, enabled: isNotClassificationTask }
    );

    useHotkeys(
        hotkeys.copyAnnotation,
        (event) => {
            if (isNonEmptyArray(selectedAnnotations) && selectedMediaItem !== undefined) {
                event.preventDefault();

                mediaId.current = getMediaId(selectedMediaItem);
                setLsAnnotations(selectedAnnotations);
            }
        },
        { ...HOTKEY_OPTIONS, enabled: isNotClassificationTask },
        [selectedAnnotations, selectedMediaItem]
    );

    useHotkeys(
        hotkeys.pasteAnnotation,
        (event) => {
            if (lsAnnotations === null || selectedMediaItem === undefined) {
                return;
            }

            event.preventDefault();

            const hasInvalidLabels = lsAnnotations.some(
                (annotation) => hasValidLabelsAndStructure(taskLabels, annotation) === false
            );

            if (hasInvalidLabels) {
                addNotification({
                    message: 'You can only paste annotations in the same task context.',
                    type: NOTIFICATION_TYPE.INFO,
                });
                return;
            }

            if (!canHaveMultipleAnnotations && hasMultipleAnnotations) {
                addNotification({
                    message: 'Multiple annotations are not allowed for this task.',
                    type: NOTIFICATION_TYPE.INFO,
                });
                return;
            }

            const areAnnotationsPastedToTheSameMedia = mediaId.current === getMediaId(selectedMediaItem);

            const offsetFactor = areAnnotationsPastedToTheSameMedia ? pasteCounter.current + 1 : pasteCounter.current;

            const offset = (OFFSET / zoom) * offsetFactor;

            const translatedAnnotations = lsAnnotations.map((annotation) => {
                const translateVector = getTranslateVector(
                    getCenterOfShape(annotation.shape),
                    image.width,
                    image.height,
                    offset
                );

                return translateAnnotation(annotation, translateVector);
            });

            const annotationsInsideROI = translatedAnnotations.filter(
                ({ shape }) => isShapePartiallyWithinROI(roi, shape) || isShapeWithinRoi(roi, shape)
            );

            const intersectedAnnotations = annotationsInsideROI.map((annotation) => ({
                ...annotation,
                shape: removeOffLimitPoints(annotation.shape, roi),
            }));

            const newAnnotations = intersectedAnnotations.map(({ shape, labels }) => {
                const newLabels = labels.map((label) =>
                    isPrediction(label) ? labelFromUser(label, activeUser?.id) : label
                );

                return {
                    ...createAnnotation(shape, newLabels),
                    isSelected: true,
                };
            });

            if (newAnnotations.length > 0) {
                scene.addAnnotations(newAnnotations);
            }

            if (intersectedAnnotations.length < translatedAnnotations.length) {
                addNotification({
                    message: `One or more annotations outside the region of interest haven't been pasted.`,
                    type: NOTIFICATION_TYPE.INFO,
                });
            }

            pasteCounter.current++;
        },
        { ...HOTKEY_OPTIONS, enabled: isNotClassificationTask && activeUser !== undefined },
        [taskLabels, lsAnnotations, roi, selectedMediaItem, scene]
    );

    useEffect(() => {
        if (selectedMediaItem) {
            pasteCounter.current = 0;
        }
    }, [selectedMediaItem, lsAnnotations]);
};
