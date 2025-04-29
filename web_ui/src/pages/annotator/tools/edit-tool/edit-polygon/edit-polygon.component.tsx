// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef, useState } from 'react';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Polygon } from '../../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../../core/annotations/shapetype.enum';
import { Labels } from '../../../annotation/labels/labels.component';
import { AnnotationScene } from '../../../core/annotation-scene.interface';
import { AnnotationToolContext, ToolType } from '../../../core/annotation-tool-context.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../../zoom/zoom-provider.component';
import { SelectingToolType } from '../../selecting-tool/selecting-tool.enums';
import { isPolygonValid, removeOffLimitPointsPolygon } from '../../utils';
import { TranslateShape } from '../translate-shape.component';
import { EditPoints } from './edit-points.component';

import classes from './../../../annotator-canvas.module.scss';

interface EditPolygonProps {
    annotationToolContext: AnnotationToolContext;
    annotation: Annotation & { shape: { shapeType: ShapeType.Polygon } };
    disableTranslation?: boolean;
    disablePoints?: boolean;
}

const updateOrRemovePolygonAnnotation = (annotation: Annotation, scene: AnnotationScene): void => {
    if (isPolygonValid(annotation.shape as Polygon)) {
        scene.updateAnnotation({ ...annotation });
    } else {
        scene.removeAnnotations([annotation]);
    }
};

export const EditPolygon = ({
    annotationToolContext,
    annotation,
    disablePoints = false,
    disableTranslation = false,
}: EditPolygonProps): JSX.Element => {
    const isAddPoint = useRef(false);
    const [shape, setShape] = useState(annotation.shape);

    useEffect(() => setShape(annotation.shape), [annotation.shape]);

    const { roi, image } = useROI();

    const { scene, tool, getToolSettings } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();

    // "removeOffLimitPoints" not only remove offlimit points but also in-between ones,
    // a new point is considered "in-between," and so it gets removed,
    // to avoid losing points we need not to use it when adding new ones
    const onComplete = (newShape: Polygon) => {
        const finalShape = isAddPoint.current ? newShape : removeOffLimitPointsPolygon(newShape, roi);

        updateOrRemovePolygonAnnotation({ ...annotation, shape: finalShape }, scene);

        isAddPoint.current = false;
    };

    const toolSettings = getToolSettings(ToolType.SelectTool);
    const isBrushSubTool = tool === ToolType.SelectTool && toolSettings?.tool === SelectingToolType.BrushTool;

    const translate = (inTranslate: { x: number; y: number }) => {
        setShape({
            ...shape,
            points: shape.points.map(({ x, y }) => ({
                x: x + inTranslate.x,
                y: y + inTranslate.y,
            })),
        });
    };

    const moveAnchorTo = (idx: number, x: number, y: number) => {
        isAddPoint.current = false;

        setShape((polygon) => ({
            ...shape,
            points: polygon.points.map((oldPoint, oldIdx) => {
                return idx === oldIdx ? { x, y } : oldPoint;
            }),
        }));
    };

    const addPoint = (idx: number, x: number, y: number) => {
        isAddPoint.current = true;

        setShape((polygon) => {
            const pointsBefore = [...polygon.points].splice(0, idx);
            const pointsAfter = [...polygon.points].splice(idx, polygon.points.length);
            const points = [...pointsBefore, { x, y }, ...pointsAfter];

            return {
                ...polygon,
                points,
            };
        });
    };

    const removePoints = (indexes: number[]): void => {
        const points = shape.points.filter((_, pointIdx) => !indexes.includes(pointIdx));

        setShape({ ...shape, points });
        onComplete({ ...shape, points });
    };

    return (
        <>
            <svg
                id={`translate-polygon-${annotation.id}`}
                className={classes.disabledLayer}
                width={image.width}
                height={image.height}
            >
                <TranslateShape
                    zoom={zoom}
                    translateShape={translate}
                    annotation={{ ...annotation, shape }}
                    onComplete={() => onComplete(shape)}
                    disabled={disableTranslation || isBrushSubTool}
                />
            </svg>

            {shape.points.length > 0 && !isBrushSubTool && (
                <Labels annotation={{ ...annotation, shape }} annotationToolContext={annotationToolContext} />
            )}

            {disablePoints === false && !isBrushSubTool ? (
                <svg
                    id={`edit-polygon-points-${annotation.id}`}
                    className={classes.disabledLayer}
                    width={image.width}
                    height={image.height}
                >
                    <EditPoints
                        shape={shape}
                        addPoint={addPoint}
                        removePoints={removePoints}
                        onComplete={() => onComplete(shape)}
                        moveAnchorTo={moveAnchorTo}
                        roi={roi}
                        zoom={zoom}
                    />
                </svg>
            ) : (
                <></>
            )}
        </>
    );
};
