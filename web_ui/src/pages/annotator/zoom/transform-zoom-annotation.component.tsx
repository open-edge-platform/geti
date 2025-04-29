// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { TransformZoom } from '../../shared/zoom/transform-zoom.component';
import { useZoomIntoAnnotation } from './use-zoom-into-annotations.hook';

export const TransformZoomAnnotation = ({ children }: { children?: ReactNode }): JSX.Element => {
    useZoomIntoAnnotation();

    return <TransformZoom>{children}</TransformZoom>;
};
