// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Annotation } from '../../../shared/types';
import { AnnotationShapeWithLabels } from './annotation-shape-with-labels.component';

interface AnnotationShapeRendererProps {
    annotation: Annotation;
    hideLabels?: boolean;
}

// `hideLabels` here is only for callers without a label-editing context (e.g. edit-polygon/
// edit-bounding-box tool previews) that must skip mounting labels entirely. The user-facing
// "hide labels" canvas setting is applied via CSS (--annotation-labels-display, see
// annotator-canvas-settings.component.tsx) so toggling it doesn't mount/unmount every annotation.
export const AnnotationShapeRenderer = ({ annotation, hideLabels = false }: AnnotationShapeRendererProps) => {
    return <AnnotationShapeWithLabels annotation={annotation} hideLabels={hideLabels} />;
};
