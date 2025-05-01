// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useRef, useState } from 'react';

import { hasEqualId } from '@shared/utils';

import { Delete, Edit, Invisible, Lock, Stamp, Unlock } from '../../../../assets/icons';
import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Point } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { getAvailableLabelsForAnnotation } from '../../annotation/labels/utils';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { useSelectingState } from '../../tools/selecting-tool/selecting-state-provider.component';
import { useROI } from '../region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../task-provider/task-provider.component';
import { useAnnotatorContextMenu } from './annotator-context-menu-provider.component';
import { AnnotationContextMenuItemsKeys } from './utils';

interface LabelsSearchConfig {
    labels: readonly Label[];
    annotation: Annotation;
    position: Point;
}

const ANNOTATION_CONTEXT_ID = 'Annotation context menu';

interface UseAnnotationContextMenu {
    annotationToolContext: AnnotationToolContext;
}

export const useAnnotationContextMenu = ({ annotationToolContext }: UseAnnotationContextMenu) => {
    const { hotkeys } = useAnnotatorHotkeys();
    const { image } = useROI();
    const [labelsSearchConfig, setLabelsSearchConfig] = useState<LabelsSearchConfig | null>(null);
    const { selectedTask, tasks } = useTask();

    const lastSelectedAnnotationId = useRef<string | null>(null);

    const { handleCreateStamp } = useSelectingState();

    const {
        addLabel,
        removeLabels,
        unselectAnnotation,
        setSelectedAnnotations,
        setLockedAnnotations,
        setHiddenAnnotations,
        removeAnnotations,
    } = annotationToolContext.scene;

    const { showContextMenu } = useAnnotatorContextMenu();

    const handleUnselectAnnotation = () => {
        if (lastSelectedAnnotationId.current === null) {
            return;
        }

        unselectAnnotation(lastSelectedAnnotationId.current);
    };

    const handleLabelSelection = (label: Label | null) => {
        if (labelsSearchConfig === null || label === null) {
            return;
        }

        const { annotation } = labelsSearchConfig;

        const hasLabel = annotation.labels.find(hasEqualId(label.id));

        if (hasLabel) {
            removeLabels([label], [annotation.id]);
        } else {
            addLabel(label, [annotation.id]);
        }

        handleUnselectAnnotation();
    };

    const handleAnnotationContextMenuAction =
        (annotation: Annotation, menuPosition: Point) =>
        (key: Key): void => {
            if (annotation === null) {
                return;
            }

            switch (key) {
                case AnnotationContextMenuItemsKeys.EDIT_LABELS: {
                    const availableLabels = getAvailableLabelsForAnnotation(
                        annotationToolContext,
                        annotation,
                        tasks,
                        selectedTask,
                        image
                    );

                    setLabelsSearchConfig({
                        labels: availableLabels,
                        annotation,
                        position: menuPosition,
                    });
                    break;
                }
                case AnnotationContextMenuItemsKeys.REMOVE: {
                    removeAnnotations([annotation]);

                    break;
                }
                case AnnotationContextMenuItemsKeys.HIDE: {
                    setHiddenAnnotations(({ id, isHidden }) =>
                        annotation.id === id ? !annotation.isHidden : isHidden
                    );

                    handleUnselectAnnotation();
                    break;
                }
                case AnnotationContextMenuItemsKeys.LOCK:
                case AnnotationContextMenuItemsKeys.UNLOCK: {
                    setLockedAnnotations(({ id, isLocked }) =>
                        annotation.id === id ? !annotation.isLocked : isLocked
                    );

                    handleUnselectAnnotation();
                    break;
                }
                case AnnotationContextMenuItemsKeys.CREATE_STAMP: {
                    handleCreateStamp([annotation]);

                    break;
                }
                default: {
                    throw new Error(`${key} action is not supported`);
                }
            }
        };

    const getAnnotationMenuItems = (annotation: Annotation) => {
        return [
            {
                id: "Annotation's actions",
                children: [
                    {
                        title: AnnotationContextMenuItemsKeys.EDIT_LABELS,
                        icon: <Edit />,
                    },
                    {
                        title: AnnotationContextMenuItemsKeys.REMOVE,
                        icon: <Delete />,
                    },
                    {
                        title: AnnotationContextMenuItemsKeys.HIDE,
                        icon: <Invisible />,
                    },
                    {
                        title: annotation?.isLocked
                            ? AnnotationContextMenuItemsKeys.UNLOCK
                            : AnnotationContextMenuItemsKeys.LOCK,
                        icon: annotation?.isLocked ? <Unlock /> : <Lock />,
                    },
                ],
            },
            {
                id: 'Create stamp tool',
                children: [
                    {
                        title: AnnotationContextMenuItemsKeys.CREATE_STAMP,
                        icon: <Stamp />,
                        shortcut: hotkeys['stamp-tool'],
                    },
                ],
            },
        ];
    };

    const handleShowAnnotationContextMenu = ({ x, y }: Point, annotation: Annotation) => {
        // set annotations as selected and show the context menu
        lastSelectedAnnotationId.current = annotation.id;

        setSelectedAnnotations(({ id }) => annotation.id === id);

        setLabelsSearchConfig(null);

        showContextMenu({
            contextId: ANNOTATION_CONTEXT_ID,
            menuItems: getAnnotationMenuItems(annotation),
            menuPosition: { top: y, left: x },
            handleMenuAction: handleAnnotationContextMenuAction(annotation, { x, y }),
            ariaLabel: ANNOTATION_CONTEXT_ID,
        });
    };

    return {
        labelsSearchConfig,
        getAnnotationMenuItems,
        handleLabelSelection,
        setLabelsSearchConfig,
        handleUnselectAnnotation,
        ANNOTATION_CONTEXT_ID,
        handleShowAnnotationContextMenu,
    };
};
