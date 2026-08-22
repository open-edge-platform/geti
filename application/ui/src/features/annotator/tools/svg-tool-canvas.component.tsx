// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { FC, PropsWithChildren, RefObject, SVGProps } from 'react';

import { roiFromImage } from '@geti-ui/smart-tools/utils';
import { useTranslation } from 'react-i18next';

import { allowPanning } from '../utils';

type CanvasProps = SVGProps<SVGSVGElement> & { image: ImageData } & { canvasRef?: RefObject<SVGRectElement | null> };
// This svg component is used to by tools that need to add local listeners that work in
// a given region of interest.
// An invisible rect is rendered to guarantee that the svg gets a width and height.
export const SvgToolCanvas: FC<PropsWithChildren<CanvasProps>> = ({
    image,
    children,
    canvasRef,
    onPointerDown,
    ...props
}) => {
    const { t } = useTranslation();
    const roi = roiFromImage(image);

    return (
        <svg
            {...props}
            style={{ ...props.style, inset: 0, position: 'absolute' }}
            onPointerDown={allowPanning(onPointerDown)}
            // eslint-disable-next-line jsx-a11y/aria-role
            role='editor'
            viewBox={`0 0 ${roi.width} ${roi.height}`}
            aria-label={props['aria-label'] ?? t('annotator.svgToolFallbackAriaLabel')}
        >
            <rect {...roi} fillOpacity={0} ref={canvasRef} />
            {children}
        </svg>
    );
};
