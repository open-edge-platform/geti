// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { hasEqualId } from '../../../../shared/utils';
import { DEFAULT_ANNOTATION_STYLES } from '../../tools/utils';
import { Annotation } from '../annotation.component';
import { LayerProps } from './utils';

import classes from '../../annotator-canvas.module.scss';

export const Layer = ({
    width,
    height,
    annotations,
    selectedTask,
    globalAnnotations,
    isOverlap = false,
    hideLabels = false,
    isPredictionMode = false,
    removeBackground = false,
    renderLabel,
}: LayerProps) => {
    const overwriteAnnotationFill = removeBackground ? { '--annotation-fill-opacity': 0 } : {};
    // We render each annotation as two layers: one where we draw its shape and another
    // where we draw its labels.
    // This is done so that we can use HTML inside the canvas (which gets tricky if you
    // try to do this inside of a svg element instead)
    return (
        <div aria-label='annotations'>
            {annotations.map((annotation) => {
                const hideAnnotationShape = globalAnnotations.some(hasEqualId(annotation.id));
                // Show labels if the annotation's shape is hidden (i.e. global empty annotations),
                // otherwise use the user's settings
                const showLabel = hideLabels === false || hideAnnotationShape;

                return (
                    <div key={annotation.id} className={classes.disabledLayer}>
                        {!hideAnnotationShape && (
                            <svg
                                width={width}
                                height={height}
                                style={{ ...DEFAULT_ANNOTATION_STYLES, ...overwriteAnnotationFill }}
                                id={`annotations-canvas-${annotation.id}-shape`}
                                aria-label={`annotations-canvas-${annotation.id}-shape`}
                            >
                                <Annotation
                                    key={annotation.id}
                                    isOverlap={isOverlap}
                                    annotation={annotation}
                                    selectedTask={selectedTask}
                                    isPredictionMode={isPredictionMode}
                                />
                            </svg>
                        )}

                        {showLabel && <div style={{ pointerEvents: 'none' }}>{renderLabel(annotation)}</div>}
                    </div>
                );
            })}
        </div>
    );
};
