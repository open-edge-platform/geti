// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { FC, PropsWithChildren, RefObject, SVGProps } from 'react';

import { useSelectedMediaItem } from '../selected-media-item-provider.component';
import { allowPanning } from '../utils';

type CanvasProps = SVGProps<SVGSVGElement> & { canvasRef?: RefObject<SVGRectElement | null> };
// Overlays the whole media so points measured against `canvasRef` are in media space; tools clamp them to the ROI.
// An invisible rect is rendered to guarantee that the svg gets a width and height.
export const SvgToolCanvas: FC<PropsWithChildren<CanvasProps>> = ({ children, canvasRef, onPointerDown, ...props }) => {
    const { mediaItem } = useSelectedMediaItem();
    const { width, height } = mediaItem;

    return (
        <svg
            {...props}
            style={{ ...props.style, inset: 0, position: 'absolute' }}
            onPointerDown={allowPanning(onPointerDown)}
            // eslint-disable-next-line jsx-a11y/aria-role
            role='editor'
            viewBox={`0 0 ${width} ${height}`}
            aria-label={props['aria-label'] ?? 'tool'}
        >
            <rect width={width} height={height} fillOpacity={0} ref={canvasRef} />
            {children}
        </svg>
    );
};
