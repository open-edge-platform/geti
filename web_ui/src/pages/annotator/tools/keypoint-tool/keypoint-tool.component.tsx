// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';

import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { Point } from '../../../../core/annotations/shapes.interface';
import { labelFromUser } from '../../../../core/annotations/utils';
import { PoseEdges } from '../../annotation/shapes/pose-edges.component';
import { PoseKeypoints } from '../../annotation/shapes/pose-keypoints.component';
import { useVisibleAnnotations } from '../../hooks/use-visible-annotations.hook';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { ResizeAnchor } from '../edit-tool/resize-anchor.component';
import { TranslateShape } from '../edit-tool/translate-shape.component';
import { getBoundingBoxInRoi, getBoundingBoxResizePoints, getClampedBoundingBox } from '../edit-tool/utils';
import { SvgToolCanvas } from '../svg-tool-canvas.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { CrosshairDrawingBox } from './crosshair-drawing-box.component';
import { useKeypointState } from './keypoint-state-provider.component';
import {
    CursorDirection,
    getAnnotationInBoundingBox,
    getInnerPaddedBoundingBox,
    getMinBoundingBox,
    MIN_BOUNDING_BOX_SIZE,
} from './utils';

export const KeypointTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { zoomState } = useZoom();
    const { image, roi } = useROI();
    const visibleAnnotations = useVisibleAnnotations();
    const { templateLabels, templatePoints, currentBoundingBox, setCurrentBoundingBox, setCursorDirection } =
        useKeypointState();

    const keypointAnnotation = currentBoundingBox
        ? getAnnotationInBoundingBox(
              templatePoints,
              getInnerPaddedBoundingBox(getMinBoundingBox(currentBoundingBox), zoomState.zoom)
          )
        : null;

    const boundingBoxResizePoints = isEmpty(currentBoundingBox)
        ? []
        : getBoundingBoxResizePoints({
              gap: MIN_BOUNDING_BOX_SIZE,
              boundingBox: currentBoundingBox,
              onResized: (newPaddedBoundingBox) => {
                  setCurrentBoundingBox(getBoundingBoxInRoi(newPaddedBoundingBox, roi), true);
              },
          });

    const handleAddAnnotation = () => {
        if (isNil(keypointAnnotation)) {
            return;
        }

        // We add a label so that the annotation doesn't get flagged as invalid by `hasInvalidAnnotations`
        // when the user submits it
        const newAnnotation = { ...keypointAnnotation, isSelected: true, labels: [labelFromUser(templateLabels[0])] };

        if (isEmpty(visibleAnnotations)) {
            annotationToolContext.scene.addAnnotations([newAnnotation]);
            setCurrentBoundingBox(null);
        }
    };

    const handleRemoveOldABoundingBox = () => {
        setCurrentBoundingBox(null);
    };

    const handleTranslate = (point: Point) => {
        currentBoundingBox && handleUpdateSkypeHistory(getClampedBoundingBox(point, currentBoundingBox, roi));
    };

    const handleUpdateSkypeHistory = (newBoundingBox: RegionOfInterest, direction?: CursorDirection) => {
        direction && setCursorDirection(direction);
        setCurrentBoundingBox(getMinBoundingBox(newBoundingBox), true);
    };

    const handleUpdateInternalHistory = () => {
        setCurrentBoundingBox(currentBoundingBox);
    };

    return (
        <SvgToolCanvas image={image}>
            <CrosshairDrawingBox
                zoom={zoomState.zoom}
                onMove={handleUpdateSkypeHistory}
                onStart={handleRemoveOldABoundingBox}
                onComplete={handleAddAnnotation}
            />

            {!isNil(keypointAnnotation) && (
                <TranslateShape
                    disabled={false}
                    zoom={zoomState.zoom}
                    annotation={keypointAnnotation}
                    onComplete={handleUpdateInternalHistory}
                    translateShape={handleTranslate}
                >
                    <PoseEdges shape={keypointAnnotation.shape} />
                    <PoseKeypoints shape={keypointAnnotation.shape} />
                </TranslateShape>
            )}

            <g style={{ pointerEvents: 'auto' }}>
                {boundingBoxResizePoints.map(({ moveAnchorTo, cursor, label, x, y }) => {
                    return (
                        <ResizeAnchor
                            key={label}
                            x={x}
                            y={y}
                            fill={'black'}
                            stroke={'white'}
                            strokeWidth={2}
                            zoom={zoomState.zoom}
                            label={label}
                            cursor={cursor}
                            onComplete={handleUpdateInternalHistory}
                            moveAnchorTo={moveAnchorTo}
                        />
                    );
                })}
            </g>
        </SvgToolCanvas>
    );
};
