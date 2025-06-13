// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, useEffect } from 'react';

import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { Line } from '../../annotation/shapes/line.component';
import { Polygon } from '../../annotation/shapes/polygon.component';
import { CircleSizePreview } from '../../components/circle-size-preview/circle-size-preview.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAddUnfinishedShape } from '../../hooks/use-add-unfinished-shape.hook';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { MarkerTool } from '../marker-tool/marker-tool.component';
import { Marker } from '../marker-tool/marker-tool.interface';
import { ToolAnnotationContextProps } from '../tools.interface';
import { drawingStyles, isPolygonValid } from '../utils';
import { BrushSizeCursor } from './brush-size-cursor.component';
import { BACKGROUND_LABEL_MARKER_ID, formatAndAddAnnotations, getScaleValue, WatershedPolygonWithLabel } from './utils';
import { useWatershedState } from './watershed-state-provider.component';

const MIN_NUMBER_OF_REQUIRED_UNIQUE_MARKERS = 2;

export const WatershedTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { getToolSettings, scene } = annotationToolContext;
    const {
        zoomState: { zoom },
    } = useZoom();
    const { roi, image } = useROI();

    const { shapes, onComplete, runWatershed, reset, setShapes, brushSize, isBrushSizePreviewVisible } =
        useWatershedState();

    useAddUnfinishedShape({
        shapes: shapes.watershedPolygons,
        addShapes: (watershedPolygons) =>
            formatAndAddAnnotations(watershedPolygons as WatershedPolygonWithLabel[], scene.addAnnotations),
        reset,
    });

    const {
        brushSize: selectedBrushSize,
        label: selectedLabel,
        sensitivity: selectedSensitivity,
    } = getToolSettings(ToolType.WatershedTool);

    const getValidPolygons = (watershedPolygon: WatershedPolygonWithLabel[]) =>
        watershedPolygon.filter(({ points }) => isPolygonValid({ shapeType: ShapeType.Polygon, points }));

    const triggerWatershed = (markers: Marker[]) => {
        // Get scaleValue based on the selected sensitivity
        const scaleValue = getScaleValue(selectedSensitivity);

        runWatershed(
            {
                imageData: image,
                markers: [...shapes.markers, ...markers],
                sensitivity: Number(scaleValue),
            },
            {
                onSuccess: (result) => {
                    setShapes((previousShapes) => ({
                        markers: [...previousShapes.markers, ...markers],
                        watershedPolygons: getValidPolygons(result),
                    }));
                },
            }
        );
    };

    const handleOnComplete = (marker: Marker) => {
        // Get number of unique markers (ids) on the canvas
        const uniqueMarkerIds = new Set([...shapes.markers, marker].map(({ id }) => id));

        // After we finish drawing, if we have at least two different markers, we run the algorithm
        if (uniqueMarkerIds.size >= MIN_NUMBER_OF_REQUIRED_UNIQUE_MARKERS) {
            triggerWatershed([marker]);
        } else {
            onComplete([marker]);
        }
    };

    useEffect(() => {
        const uniqueMarkerIds = new Set(shapes.markers.map(({ id }) => id));
        if (uniqueMarkerIds.size >= MIN_NUMBER_OF_REQUIRED_UNIQUE_MARKERS) {
            triggerWatershed([]);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedSensitivity]);

    useEffect(() => {
        // Reset markers, polygons and imageData on the watershed worker
        reset();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [image]);

    return (
        <CircleSizePreview circleSize={brushSize} roi={roi} isCircleSizePreviewVisible={isBrushSizePreviewVisible}>
            <g>
                {shapes.watershedPolygons?.length ? (
                    shapes.watershedPolygons.map(({ id, points, label }, idx) => {
                        // If there is no polygon corresponding to the marker id or if it's the background label (id 1)
                        // we shouldn't draw anything
                        if (id === BACKGROUND_LABEL_MARKER_ID || !label) {
                            return null;
                        }

                        return (
                            <Polygon
                                key={idx}
                                shape={{ shapeType: ShapeType.Polygon, points }}
                                styles={drawingStyles(label)}
                            />
                        );
                    })
                ) : (
                    <></>
                )}

                {shapes.markers.length ? (
                    shapes.markers.map(({ points, label, brushSize: brushSizeValue }, idx) => (
                        <Line
                            key={idx}
                            points={points}
                            brushSize={brushSizeValue}
                            color={label?.color}
                            style={{ opacity: 'var(--markers-opacity)' }}
                        />
                    ))
                ) : (
                    <></>
                )}

                {selectedLabel ? (
                    <MarkerTool
                        styles={{ cursor: 'none' }}
                        label={selectedLabel.label}
                        brushSize={selectedBrushSize}
                        image={image}
                        markerId={selectedLabel.markerId}
                        zoom={zoom}
                        onComplete={handleOnComplete}
                        renderCursor={(props: ComponentProps<typeof BrushSizeCursor>) => <BrushSizeCursor {...props} />}
                    />
                ) : null}
            </g>
        </CircleSizePreview>
    );
};
