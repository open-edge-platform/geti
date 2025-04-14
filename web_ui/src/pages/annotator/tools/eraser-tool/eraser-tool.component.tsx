// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, ReactNode, RefObject } from 'react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getTheTopShapeAt } from '../../../../core/annotations/utils';
import { isEraserButton } from '../../../buttons-utils';
import { getRelativePoint } from '../../../utils';
import { AnnotationScene } from './../../core/annotation-scene.interface';
import { useZoom } from './../../zoom/zoom-provider.component';
import { PointerType } from './..//tools.interface';

interface ErasableCanvasProps {
    annotations: ReadonlyArray<Annotation>;
    scene: AnnotationScene;
    canvasRef: RefObject<SVGSVGElement>;
    children: ReactNode;
}

export const EraserTool = ({ canvasRef, annotations, children, scene }: ErasableCanvasProps) => {
    const {
        zoomState: { zoom },
    } = useZoom();

    const onPointerMove = (event: PointerEvent<SVGSVGElement>): void => {
        if (canvasRef.current === null) {
            return;
        }

        const button = {
            button: event.button,
            buttons: event.buttons,
        };

        if (event.pointerType === PointerType.Pen && isEraserButton(button)) {
            const currentPoint = getRelativePoint(canvasRef.current, { x: event.clientX, y: event.clientY }, zoom);
            const topAnnotation = getTheTopShapeAt(annotations, currentPoint);

            if (topAnnotation) {
                scene.removeAnnotations([topAnnotation]);
            }
        }
    };

    return <svg onPointerMove={onPointerMove}>{children}</svg>;
};
