// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
