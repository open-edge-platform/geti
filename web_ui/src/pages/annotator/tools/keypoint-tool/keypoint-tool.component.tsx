// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
    getAnnotationInBoundingBox,
    getInnerPaddedBoundingBox,
    getMinBoundingBox,
    MIN_BOUNDING_BOX_SIZE,
} from './utils';

export const KeypointTool = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { zoomState } = useZoom();
    const { image, roi } = useROI();
    const visibleAnnotations = useVisibleAnnotations();
    const { templateLabels, templatePoints, currentBoundingBox, setCurrentBoundingBox } = useKeypointState();

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

    const handleUpdateSkypeHistory = (newBoundingBox: RegionOfInterest) => {
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
