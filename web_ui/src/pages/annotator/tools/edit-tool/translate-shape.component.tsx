// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, ReactNode, useState } from 'react';

import { Annotation as AnnotationInterface } from '../../../../core/annotations/annotation.interface';
import { Point } from '../../../../core/annotations/shapes.interface';
import { isLeftButton } from '../../../buttons-utils';
import { Annotation } from '../../annotation/annotation.component';
import { PointerType } from '../tools.interface';
import { allowPanning } from '../utils';

const STROKE_WIDTH = 2;

interface TranslateShapeProps {
    zoom: number;
    annotation: AnnotationInterface;
    translateShape: ({ x, y }: { x: number; y: number }) => void;
    onComplete: () => void;
    disabled: boolean;
    children?: ReactNode;
}

export const TranslateShape = ({
    zoom,
    disabled,
    annotation,
    onComplete,
    translateShape,
    children = <Annotation annotation={annotation} />,
}: TranslateShapeProps): JSX.Element => {
    const [dragFromPoint, setDragFromPoint] = useState<null | Point>(null);

    const onPointerDown = (event: PointerEvent<SVGSVGElement>): void => {
        if (dragFromPoint !== null) {
            return;
        }

        if (event.pointerType === PointerType.Touch || !isLeftButton(event)) {
            return;
        }

        const mouse = { x: Math.round(event.clientX / zoom), y: Math.round(event.clientY / zoom) };

        event.currentTarget.setPointerCapture(event.pointerId);

        setDragFromPoint(mouse);
    };

    const onPointerMove = (event: PointerEvent<SVGSVGElement>) => {
        event.preventDefault();

        if (dragFromPoint === null) {
            return;
        }

        const mouse = { x: Math.round(event.clientX / zoom), y: Math.round(event.clientY / zoom) };

        translateShape({
            x: mouse.x - dragFromPoint.x,
            y: mouse.y - dragFromPoint.y,
        });
        setDragFromPoint(mouse);
    };

    const onPointerUp = (event: PointerEvent<SVGSVGElement>) => {
        if (dragFromPoint === null) {
            return;
        }
        event.preventDefault();
        setDragFromPoint(null);
        event.currentTarget.releasePointerCapture(event.pointerId);
        onComplete();
    };

    return (
        <g
            id={`translate-annotation-${annotation.id}`}
            stroke='var(--energy-blue)'
            strokeWidth={STROKE_WIDTH / zoom}
            aria-label='Drag to move shape'
            onPointerDown={allowPanning(onPointerDown)}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerUp}
            style={disabled ? {} : { pointerEvents: 'auto', cursor: 'move' }}
        >
            {children}
        </g>
    );
};
