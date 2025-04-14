// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MutableRefObject } from 'react';

import { Point, Polygon, Shape } from '../../../../core/annotations/shapes.interface';
import { isRect } from '../../../../core/annotations/utils';
import { runWhenTruthy } from '../../../../shared/utils';
import { Line } from '../../annotation/shapes/line.component';
import { Rectangle } from '../../annotation/shapes/rectangle.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAddUnfinishedShape } from '../../hooks/use-add-unfinished-shape.hook';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { DrawingBox } from '../drawing-box/drawing-box.component';
import { MarkerTool } from '../marker-tool/marker-tool.component';
import { Marker } from '../marker-tool/marker-tool.interface';
import { PolygonDraw } from '../polygon-draw.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles, GRABCUT_RESULT_BOX_STYLES, SELECT_ANNOTATION_STYLES } from '../utils';
import { useGrabcutState } from './grabcut-state-provider.component';
import { GrabcutToolIconsOffset, GrabcutToolType } from './grabcut-tool.enums';
import { calcStrokeWidth, getLabel, isBackgroundTool, isForegroundTool } from './util';

import classes from './grabcut-tool.module.scss';

interface Markers {
    marker: Point[][];
    color: string;
    ariaLabel: string;
}

const ShowMarkers = ({ markers, strokeWidth }: { markers: [Markers, Markers]; strokeWidth: number }): JSX.Element => (
    <>
        {markers?.map(({ marker, color, ariaLabel }) =>
            marker?.map((points, idx) => {
                return (
                    <Line
                        key={`line-${idx}`}
                        color={color}
                        points={points}
                        brushSize={strokeWidth}
                        ariaLabel={ariaLabel}
                        style={{ opacity: 'var(--markers-opacity)' }}
                    />
                );
            })
        )}
    </>
);

export const GrabcutTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { defaultLabel } = useTask();
    const { image } = useROI();
    const { scene, getToolSettings } = annotationToolContext;
    const { sensitivity } = getToolSettings(ToolType.GrabcutTool);
    const {
        zoomState: { zoom },
    } = useZoom();

    const {
        toolsState,
        loadingRect,
        isLoading,
        runGrabcut,
        resetConfig,
        setDrawingToFalse,
        foregroundMarkers,
        backgroundMarkers,
    } = useGrabcutState();

    useAddUnfinishedShape({
        shapes: toolsState?.polygon ? [toolsState.polygon] : [],
        addShapes: (polygonShape) => scene.addShapes(polygonShape as Shape[]),
        reset: resetConfig,
    });

    const strokeWidth = calcStrokeWidth(toolsState.inputRect?.width ?? 0);

    const onRectComplete = (shape: Shape) => {
        resetConfig();
        acceptPrevShape(toolsState.polygon);

        if (isRect(shape)) {
            loadingRect.current = shape;

            runGrabcut(image, strokeWidth, sensitivity);
        }
    };

    const onStrokeComplete = (marker: MutableRefObject<Point[][]>) => (newMarker: Marker) => {
        marker.current.push(newMarker.points);
        runGrabcut(image, strokeWidth, sensitivity);
    };

    const acceptPrevShape = runWhenTruthy((prevPolygon: Polygon): void => {
        scene.addShapes([prevPolygon], undefined, false);
    });

    // markers must be applied in a specific order depending on the currently active tool,
    // if the activeTool is ForegroundTool- first apply backgroundMarkers and then apply foregroundMarkers
    const foregroundMarkerAndColor = {
        marker: toolsState.foreground,
        color: ' var(--brand-moss)',
        ariaLabel: 'foreground-marker',
    };
    const backgroundMarkerAndColor = {
        marker: toolsState.background,
        color: 'var(--brand-coral-cobalt)',
        ariaLabel: 'background-marker',
    };
    const markersByToolType: { [Key: string]: [Markers, Markers] } = {
        [GrabcutToolType.ForegroundTool]: [backgroundMarkerAndColor, foregroundMarkerAndColor],
        [GrabcutToolType.BackgroundTool]: [foregroundMarkerAndColor, backgroundMarkerAndColor],
    };

    return (
        <>
            {toolsState.polygon?.points.length && (
                <PolygonDraw
                    indicatorRadius={0}
                    shape={toolsState.polygon}
                    ariaLabel='grabcut-polygon'
                    className={isLoading ? classes.inputTool : ''}
                    styles={drawingStyles(defaultLabel)}
                />
            )}
            {toolsState.activeTool === GrabcutToolType.InputTool && (
                <>
                    {!isLoading && (
                        <DrawingBox
                            zoom={zoom}
                            image={image}
                            withCrosshair={true}
                            onStart={setDrawingToFalse}
                            onComplete={onRectComplete}
                            styles={SELECT_ANNOTATION_STYLES}
                        />
                    )}
                    {loadingRect?.current && isLoading && (
                        <Rectangle
                            shape={loadingRect.current}
                            ariaLabel='loading-roi-rect'
                            styles={{ ...SELECT_ANNOTATION_STYLES, className: classes.inputTool }}
                        />
                    )}
                </>
            )}

            {toolsState.inputRect && !isLoading && (
                <Rectangle
                    ariaLabel='roi-rect'
                    shape={toolsState.inputRect}
                    styles={{ ...GRABCUT_RESULT_BOX_STYLES }}
                />
            )}

            {(isForegroundTool(toolsState.activeTool) || isBackgroundTool(toolsState.activeTool)) && (
                <ShowMarkers markers={markersByToolType[toolsState.activeTool]} strokeWidth={strokeWidth}></ShowMarkers>
            )}

            {isForegroundTool(toolsState.activeTool) && toolsState.inputRect && (
                <MarkerTool
                    markerId={0}
                    image={image}
                    zoom={zoom}
                    brushSize={strokeWidth}
                    roi={toolsState.inputRect}
                    label={getLabel('foreground', 'var(--brand-moss)')}
                    onComplete={onStrokeComplete(foregroundMarkers)}
                    styles={{
                        cursor: `url(/icons/cursor/pencil-plus.svg) ${GrabcutToolIconsOffset.Foreground}, auto`,
                    }}
                />
            )}
            {isBackgroundTool(toolsState.activeTool) && toolsState.inputRect && (
                <MarkerTool
                    markerId={1}
                    image={image}
                    zoom={zoom}
                    brushSize={strokeWidth}
                    roi={toolsState.inputRect}
                    label={getLabel('background', 'var(--brand-coral-cobalt')}
                    onComplete={onStrokeComplete(backgroundMarkers)}
                    styles={{
                        cursor: `url(/icons/cursor/pencil-minus.svg) ${GrabcutToolIconsOffset.Background}, auto`,
                    }}
                />
            )}
        </>
    );
};
