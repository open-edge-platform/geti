// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { PointerEvent, useRef, useState } from 'react';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { clampBox, clampPointBetweenImage, isPointInShape, pointInRectangle } from '../../../../core/annotations/math';
import { Rect } from '../../../../core/annotations/shapes.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { isPoseShape, isRect } from '../../../../core/annotations/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { isRightButton } from '../../../buttons-utils';
import { getRelativePoint } from '../../../utils';
import { Circle } from '../../annotation/shapes/circle.component';
import { Polygon } from '../../annotation/shapes/polygon.component';
import { Rectangle } from '../../annotation/shapes/rectangle.component';
import { RotatedRectangle } from '../../annotation/shapes/rotated-rectangle.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTaskChain } from '../../providers/task-chain-provider/task-chain-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { DrawingBox } from '../drawing-box/drawing-box.component';
import { SvgToolCanvas } from '../svg-tool-canvas.component';
import { PointerType, ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles } from '../utils';
import { LoadingAnimation } from './loading-animation.component';
import { useRITMState } from './ritm-state-provider.component';
import { RITMPoint, RITMResult, TEMPLATE_SIZE } from './ritm-tool.interface';
import { encapsulatePoints } from './util';

import classes from './ritm.module.scss';

// Adding 1 to prevent template_size, and box size being exact same size, causing some issues.
const MINIMUM_MARGIN = TEMPLATE_SIZE / 2 + 1;

export const RITMTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { defaultLabel, activeDomains } = useTask();
    const { getToolSettings } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();

    const hasRotatedBoundingBoxDomain = activeDomains.includes(DOMAIN.DETECTION_ROTATED_BOUNDING_BOX);
    const outputShape = hasRotatedBoundingBoxDomain ? ShapeType.RotatedRect : ShapeType.Polygon;

    const { image } = useROI();
    const clampPoint = clampPointBetweenImage(image);
    const { addShapes } = annotationToolContext.scene;

    const imageROI = { x: 0, y: 0, width: image.width, height: image.height };
    const { inputs } = useTaskChain();
    const ROI: RegionOfInterest =
        (inputs.find(({ isSelected, shape }) => isSelected && isRect(shape))?.shape as Rect) || imageROI;

    const ref = useRef<SVGRectElement>(null);

    const { result, execute, reset, box, setBox, isProcessing, isLoading, cancel } = useRITMState();

    const lowestImageSide = Math.min(image.width, image.height);

    const styles = drawingStyles(defaultLabel);

    const ritmConfig = getToolSettings(ToolType.RITMTool);

    const boxDrawn = box && !ritmConfig.dynamicBoxMode;
    const isDrawingBox = !ritmConfig.dynamicBoxMode && !box;

    const [lastPoint, setLastPoint] = useState<RITMPoint | null>(null);

    const cursorOffset = ritmConfig.rightClickMode ? '7 8' : '16 16';

    const onPointerUp = (event: PointerEvent<SVGSVGElement>) => {
        if (!ref.current || isLoading) {
            return;
        }

        if (event.button !== 0 && event.button !== 2) {
            return;
        }

        if (event.pointerType === PointerType.Touch) {
            return;
        }

        if (event.detail > 1) {
            cancel();

            return;
        }

        if (!ritmConfig.rightClickMode && isRightButton({ button: event.button, buttons: event.buttons })) {
            return;
        }

        const { x, y } = clampPoint(getRelativePoint(ref.current, { x: event.clientX, y: event.clientY }, zoom));
        const pointInCurrentBox = !!result && !!result.shape && isPointInShape(result.shape, { x, y });
        const positive = ritmConfig.rightClickMode ? event.button === 0 : !pointInCurrentBox;

        if (ritmConfig.dynamicBoxMode) {
            const margin = Math.max(lowestImageSide / 4, MINIMUM_MARGIN);

            const newPoint = { x, y, positive };

            const points = result !== null ? [...result.points, newPoint] : [newPoint];

            const foundBox = clampBox(encapsulatePoints(points, margin), ROI);

            executeRITM(x, y, positive, foundBox);
        } else {
            if (box) {
                if (pointInRectangle(box, { x, y })) {
                    executeRITM(x, y, positive, box);
                } else {
                    if (result && result.shape) {
                        addShapes([result.shape]);
                        reset();
                    }

                    setBox(null);
                }
            }
        }
    };

    const executeRITM = (x: number, y: number, positive: boolean, currentBox: RegionOfInterest) => {
        if (isProcessing || !pointInRectangle(currentBox, { x, y })) {
            return;
        }

        setLastPoint({ x, y, positive });
        setBox(currentBox);

        const newPoint = { x, y, positive };
        const points = result ? [...result.points, newPoint] : [newPoint];

        execute(image, clampBox(currentBox, ROI), points, outputShape);
    };

    const renderResult = ({ shape }: RITMResult): JSX.Element => {
        if (shape === undefined || isPoseShape(shape)) {
            return <></>;
        }

        const ariaLabel = 'result shape';
        const cursorName = ritmConfig.rightClickMode ? 'selection' : 'pencil-minus';
        const shapeStyles = {
            ...styles,
            cursor: `url(/icons/cursor/${cursorName}.svg) ${cursorOffset}, auto`,
        };

        switch (shape.shapeType) {
            case ShapeType.Rect:
                return <Rectangle shape={shape} ariaLabel={ariaLabel} styles={shapeStyles} />;
            case ShapeType.RotatedRect:
                return <RotatedRectangle shape={shape} ariaLabel={ariaLabel} styles={shapeStyles} />;
            case ShapeType.Circle:
                return <Circle shape={shape} ariaLabel={ariaLabel} styles={shapeStyles} />;
            case ShapeType.Polygon:
                return <Polygon shape={shape} ariaLabel={ariaLabel} styles={shapeStyles} />;
        }
    };

    const renderPoint = ({ x, y, positive }: RITMPoint, index: number): JSX.Element => {
        const fill = positive ? 'green' : 'red';

        return (
            <Circle
                key={`point-${index}`}
                shape={{ shapeType: ShapeType.Circle, x, y, r: 5 / zoom }}
                styles={{ fill, opacity: 'var(--markers-opacity)' }}
                data-testid={`point-${positive ? 'positive' : 'negative'}-${index}`}
            />
        );
    };

    const renderLoadingPoint = ({ x, y, positive }: RITMPoint): JSX.Element => {
        const fill = positive ? 'green' : 'red';

        return (
            <>
                <Circle
                    key={'loading-point'}
                    shape={{ shapeType: ShapeType.Circle, x, y, r: 5 / zoom }}
                    styles={{ fill }}
                    data-testid={'loading-point'}
                />
                <LoadingAnimation x={x} y={y} radius={1 / zoom} />
            </>
        );
    };

    const onDrawingBoxComplete = ({ x, y, width, height }: Rect) => {
        setBox({ x, y, width, height });
    };

    const cursor = ritmConfig.rightClickMode ? 'selection' : 'pencil-plus';

    return (
        <>
            {isDrawingBox ? (
                <DrawingBox withCrosshair image={image} zoom={zoom} onComplete={onDrawingBoxComplete} styles={styles} />
            ) : (
                <SvgToolCanvas
                    image={image}
                    canvasRef={ref}
                    onMouseUp={onPointerUp}
                    style={{ cursor: `url(/icons/cursor/${cursor}.svg) ${cursorOffset}, auto` }}
                >
                    {result && renderResult(result)}

                    {boxDrawn ? (
                        <Rectangle
                            shape={{ shapeType: ShapeType.Rect, ...box }}
                            styles={{ ...styles, fill: 'none', role: 'application' }}
                            className={classes.inputTool}
                        />
                    ) : null}

                    {result && result.points.map((point, index) => renderPoint(point, index))}
                    {isProcessing && lastPoint && renderLoadingPoint(lastPoint)}
                </SvgToolCanvas>
            )}
        </>
    );
};
