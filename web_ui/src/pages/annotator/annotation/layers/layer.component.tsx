// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Annotation as AnnotationInterface } from '../../../../core/annotations/annotation.interface';
import { hasEqualId } from '../../../../shared/utils';
import { DEFAULT_ANNOTATION_STYLES } from '../../tools/utils';
import { Annotation } from '../annotation.component';
import { ShapeFactory } from '../shapes/factory.component';
import { LayerProps } from './utils';

import classes from '../../annotator-canvas.module.scss';

const isHoleMask = (annotation: AnnotationInterface) => annotation.labels.some(({ name }) => name === 'background');

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

    let savedMasks: AnnotationInterface[] = [];

    return (
        <div aria-label='annotations'>
            {annotations.map((annotation) => {
                const hideAnnotationShape = globalAnnotations.some(hasEqualId(annotation.id));
                // Show labels if the annotation's shape is hidden (i.e. global empty annotations),
                // otherwise use the user's settings
                const showLabel = hideLabels === false || hideAnnotationShape;
                const maskId = `${annotation.id}-mask`;

                savedMasks = isHoleMask(annotation) ? [...savedMasks, annotation] : savedMasks;

                return (
                    <div key={annotation.id} className={classes.disabledLayer}>
                        {/* {!hideAnnotationShape && ( */}
                        {!hideAnnotationShape && (
                            <svg
                                width={width}
                                height={height}
                                style={{ ...DEFAULT_ANNOTATION_STYLES, ...overwriteAnnotationFill }}
                                id={`annotations-canvas-${annotation.id}-shape`}
                                aria-label={`annotations-canvas-${annotation.id}-shape`}
                            >
                                {<HoleMasks id={maskId} masks={savedMasks} />}

                                <Annotation
                                    key={annotation.id}
                                    isOverlap={isOverlap}
                                    annotation={annotation}
                                    selectedTask={selectedTask}
                                    isPredictionMode={isPredictionMode}
                                    maskId={`url(#${maskId})`}
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

const HoleMasks = ({ id, masks }: { id: string; masks: AnnotationInterface[] }) => {
    return (
        <defs xmlns='http://www.w3.org/2000/svg'>
            <mask id={id}>
                <rect width='100%' height='100%' fill='white' />
                <g fill='black' fillOpacity='1'>
                    {masks.map((mask) => (
                        <ShapeFactory key={mask.id} annotation={mask} />
                    ))}
                </g>
            </mask>
        </defs>
    );
};
