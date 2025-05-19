// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MutableRefObject, RefObject, useRef } from 'react';

import { View } from '@geti/ui';
import { Overlay } from '@react-spectrum/overlays';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { pointInRectangle } from '../../../../core/annotations/math';
import { getTheTopShapeAt } from '../../../../core/annotations/utils';
import { useEventListener } from '../../../../hooks/event-listener/event-listener.hook';
import { MouseEvents } from '../../../../shared/mouse-events/mouse.interface';
import { getRelativePoint } from '../../../utils';
import { LabelSearch } from '../../components/labels/label-search/label-search.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useAnnotatorContextMenu } from '../../providers/annotator-context-menu-provider/annotator-context-menu-provider.component';
import { useIsSelectionToolActive } from '../../tools/selecting-tool/selecting-state-provider.component';
import { SelectingToolType } from '../../tools/selecting-tool/selecting-tool.enums';
import { useZoom } from '../../zoom/zoom-provider.component';
import { useAnnotationContextMenu } from './use-annotation-context-menu.hook';
import { useToolContextMenu } from './use-tool-context-menu.hook';

interface AnnotationContextMenuProps {
    containerCanvasRef: RefObject<HTMLDivElement>;
    annotations: Annotation[];
    annotationToolContext: AnnotationToolContext;
    disableAnnotationContextMenu?: boolean;
}

export const AnnotationContextMenu = ({
    annotations,
    containerCanvasRef,
    annotationToolContext,
    disableAnnotationContextMenu = true,
}: AnnotationContextMenuProps): JSX.Element => {
    const overlayRef = useRef(null);
    const isStampToolActive = useIsSelectionToolActive(SelectingToolType.StampTool);
    const {
        labelsSearchConfig,
        handleLabelSelection,
        setLabelsSearchConfig,
        handleUnselectAnnotation,
        handleShowAnnotationContextMenu,
        ANNOTATION_CONTEXT_ID,
    } = useAnnotationContextMenu({
        annotationToolContext,
    });

    const { handleShowToolContextMenu } = useToolContextMenu({ annotationToolContext });

    const {
        zoomState: { zoom },
    } = useZoom();

    const { hideContextMenu, contextConfig } = useAnnotatorContextMenu();

    const isClickInsideAnnotation = (event: MouseEvent): Annotation | null => {
        if (containerCanvasRef.current === null) {
            return null;
        }

        const { clientX, clientY } = event;
        const mousePosition = {
            x: clientX,
            y: clientY,
        };
        const relativePoint = getRelativePoint(containerCanvasRef.current, mousePosition, zoom);
        return getTheTopShapeAt(annotations, relativePoint, false);
    };

    const handleContextMenu = (event: MouseEvent) => {
        event.preventDefault();

        const mousePosition = { x: event.clientX, y: event.clientY };

        if (isStampToolActive) {
            handleShowToolContextMenu(mousePosition);
        } else {
            // check if the click is inside the annotation
            const isAnnotationClicked = isClickInsideAnnotation(event);

            const isClickOutsideAnnotation = (): boolean => {
                // if click is outside the annotation and the annotation had a menu before,
                // we want to unselect the annotation and hide the menu
                if (isAnnotationClicked === null && contextConfig.contextId === ANNOTATION_CONTEXT_ID) {
                    handleUnselectAnnotation();
                    hideContextMenu();

                    return true;
                }

                // if click is outside the annotation and there was no menu, do nothing
                return isAnnotationClicked === null;
            };

            const isClickOutside = isClickOutsideAnnotation();

            if (isClickOutside) {
                handleShowToolContextMenu(mousePosition);
                return;
            }

            if (disableAnnotationContextMenu && isAnnotationClicked !== null) {
                handleShowAnnotationContextMenu(mousePosition, isAnnotationClicked);
            }
        }
    };

    const handleGlobalContextMenu = (event: MouseEvent): void => {
        const canvas = document.getElementById('canvas')?.getBoundingClientRect();

        if (canvas === undefined) {
            return;
        }

        const { clientX, clientY } = event;
        const { x, y, width, height } = canvas;

        const isClickInsideCanvas = pointInRectangle({ x, y, width, height }, { x: clientX, y: clientY });

        if (isClickInsideCanvas) {
            event.preventDefault();
        } else {
            hideContextMenu();
        }
    };

    useEventListener(MouseEvents.ContextMenu, handleContextMenu, document.getElementById('canvas'));

    useEventListener(MouseEvents.ContextMenu, handleGlobalContextMenu);

    return labelsSearchConfig === null ? (
        <></>
    ) : (
        <Overlay isOpen nodeRef={overlayRef as unknown as MutableRefObject<HTMLElement>}>
            <View position={'absolute'} top={labelsSearchConfig.position.y} left={labelsSearchConfig.position.x}>
                <LabelSearch
                    labels={labelsSearchConfig.labels}
                    onClick={handleLabelSelection}
                    onClose={() => setLabelsSearchConfig(null)}
                />
            </View>
        </Overlay>
    );
};
