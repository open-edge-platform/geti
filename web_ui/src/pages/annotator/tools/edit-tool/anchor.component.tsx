// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, PointerEvent, ReactNode, useState } from 'react';

import isFunction from 'lodash/isFunction';

import { Point } from '../../../../core/annotations/shapes.interface';
import { isLeftButton } from '../../../buttons-utils';
import { PointerType } from '../tools.interface';

interface AnchorProps {
    children: ReactNode;
    x: number;
    y: number;
    size: number;
    zoom: number;
    label: string;
    fill?: string;
    cursor?: CSSProperties['cursor'];
    onStart?: () => void;
    onComplete: () => void;
    moveAnchorTo: (x: number, y: number) => void;
}

export const Anchor = ({
    x,
    y,
    fill = 'white',
    size,
    zoom,
    label,
    cursor,
    children,
    onStart,
    moveAnchorTo,
    onComplete,
}: AnchorProps): JSX.Element => {
    const [dragFrom, setDragFrom] = useState<Point | null>(null);

    const onPointerDown = (event: PointerEvent) => {
        event.preventDefault();

        if (event.pointerType === PointerType.Touch || !isLeftButton(event)) {
            return;
        }

        event.currentTarget.setPointerCapture(event.pointerId);

        const mouse = { x: Math.round(event.clientX / zoom), y: Math.round(event.clientY / zoom) };

        isFunction(onStart) && onStart();
        setDragFrom({ x: mouse.x - x, y: mouse.y - y });
    };

    const onPointerMove = (event: PointerEvent) => {
        event.preventDefault();

        if (dragFrom === null) {
            return;
        }

        const mouse = { x: Math.round(event.clientX / zoom), y: Math.round(event.clientY / zoom) };

        moveAnchorTo(mouse.x - dragFrom.x, mouse.y - dragFrom.y);
    };

    const onPointerUp = (event: PointerEvent) => {
        if (event.pointerType === PointerType.Touch || !isLeftButton(event)) {
            return;
        }

        event.preventDefault();
        event.currentTarget.releasePointerCapture(event.pointerId);

        setDragFrom(null);
        onComplete();
    };

    // We render both a visual anchor and an invisible anchor that has a larger
    // clicking area than the visible one
    const interactiveAnchorProps = {
        style: { cursor },
        fill: dragFrom === null ? fill : 'var(--energy-blue)',
        'aria-label': label,
        onPointerUp,
        onPointerMove,
        onPointerDown,
    };

    return (
        <g>
            {children}
            <rect
                x={x - size}
                y={y - size}
                cx={x}
                cy={y}
                width={size * 2}
                height={size * 2}
                fillOpacity={0}
                {...interactiveAnchorProps}
            />
        </g>
    );
};
