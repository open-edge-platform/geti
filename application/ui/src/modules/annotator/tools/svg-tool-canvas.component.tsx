// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { FC, PropsWithChildren, RefObject, SVGProps } from 'react';

import type { RegionOfInterest } from '../../../shared/types';
import { allowPanning } from '../utils';

type CanvasProps = SVGProps<SVGSVGElement> & { roi: RegionOfInterest } & {
    canvasRef?: RefObject<SVGRectElement | null>;
};
// This svg component is used to by tools that need to add local listeners that work in
// a given region of interest.
// An invisible rect is rendered to guarantee that the svg gets a width and height.
export const SvgToolCanvas: FC<PropsWithChildren<CanvasProps>> = ({
    roi,
    children,
    canvasRef,
    onPointerDown,
    ...props
}) => {
    return (
        <svg
            {...props}
            style={{ ...props.style, inset: 0, position: 'absolute' }}
            onPointerDown={allowPanning(onPointerDown)}
            // eslint-disable-next-line jsx-a11y/aria-role
            role='editor'
            viewBox={`0 0 ${roi.width} ${roi.height}`}
            aria-label={props['aria-label'] ?? 'tool'}
        >
            <rect {...roi} fillOpacity={0} ref={canvasRef} />
            {children}
        </svg>
    );
};
