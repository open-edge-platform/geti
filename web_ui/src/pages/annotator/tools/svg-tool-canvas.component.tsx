// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
