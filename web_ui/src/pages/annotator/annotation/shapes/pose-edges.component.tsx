// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment } from 'react';

import clsx from 'clsx';
import { isNil } from 'lodash-es';

import { BoundingBox, getBoundingBox } from '../../../../core/annotations/math';
import { isKeypointTask } from '../../../../core/projects/utils';
import { useSelected } from '../../../../providers/selected-provider/selected-provider.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
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
