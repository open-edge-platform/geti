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

import { Fragment } from 'react';

import clsx from 'clsx';
import isNil from 'lodash/isNil';

import { BoundingBox, getBoundingBox } from '../../../../core/annotations/math';
import { isKeypointTask } from '../../../../core/projects/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useSelected } from '../../providers/selected-provider/selected-provider.component';
import { getOuterPaddedBoundingBox, getPointsEdges } from '../../tools/keypoint-tool/utils';
import { useZoom } from '../../zoom/zoom-provider.component';
import { KeypointProps } from './shape.interface';

import classes from './pose-edges.module.scss';

interface PoseEdgesProps extends KeypointProps {
    boundingBox?: BoundingBox;
    showBoundingBox?: boolean;
}

export const PoseEdges = ({ shape, boundingBox, showBoundingBox = true }: PoseEdgesProps): JSX.Element => {
    const { project } = useProject();
    const { zoomState } = useZoom();
    const { isSelected } = useSelected();
    const keypointTask = project.tasks.find(isKeypointTask);

    const outerPaddedBoundingBox = isNil(boundingBox)
        ? getOuterPaddedBoundingBox(getBoundingBox(shape), zoomState.zoom)
        : boundingBox;

    const selectedPoints = shape.points.filter(({ label, isVisible }) => isSelected(label.id) && isVisible);
    const edges = keypointTask !== undefined ? getPointsEdges(shape.points, keypointTask.keypointStructure.edges) : [];

    return (
        <>
            {showBoundingBox && (
                <>
                    <rect {...outerPaddedBoundingBox} className={clsx(classes.boundingBox, classes.whiteDash)} />
                    <rect {...outerPaddedBoundingBox} className={clsx(classes.boundingBox, classes.blackDash)} />
                </>
            )}

            {edges.map(({ from, to }) => {
                const selectedEdge = selectedPoints.find(
                    ({ label }) => label.id === from.labelId || label.id === to.labelId
                );
                const { opacity, stroke } =
                    selectedEdge !== undefined
                        ? { opacity: 0.5, stroke: selectedEdge.label.color }
                        : { opacity: 1, stroke: 'var(--spectrum-gray-900)' };

                return (
                    <Fragment key={`edge-${from.labelId}-${to.labelId}`}>
                        <line
                            x1={from.x}
                            x2={to.x}
                            y1={from.y}
                            y2={to.y}
                            style={{ opacity, stroke }}
                            className={clsx(classes.edge)}
                        />
                    </Fragment>
                );
            })}
        </>
    );
};
