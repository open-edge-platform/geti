// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, PropsWithChildren, RefObject, SVGProps } from 'react';

import { roiFromImage } from '../../../core/annotations/math';
import { allowPanning } from './utils';

type CanvasProps = SVGProps<SVGSVGElement> & { image: ImageData } & { canvasRef?: RefObject<SVGRectElement> };
// This svg component is used to by tools that need to add local listeners that work in
// a given region of interest.
// An invisible rect is rendered to guarantee that the svg gets a width and height.
export const SvgToolCanvas: FC<PropsWithChildren<CanvasProps>> = ({
    image,
    children,
    canvasRef,
    onPointerDown,
    ...props
}): JSX.Element => {
    const roi = roiFromImage(image);

    return (
        <svg
            {...props}
            onPointerDown={allowPanning(onPointerDown)}
            // eslint-disable-next-line jsx-a11y/aria-role
            role='editor'
            viewBox={`0 0 ${roi.width} ${roi.height}`}
        >
            <rect {...roi} fillOpacity={0} ref={canvasRef} />
            {children}
        </svg>
    );
};
