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

import { Point } from '../../../../../core/annotations/shapes.interface';

import classes from './edge.module.scss';

interface GhostLineEdgeProps {
    to: Point;
    from: Point;
}

export const GhostLineEdge = ({ to, from }: GhostLineEdgeProps) => {
    return (
        <g style={{ pointerEvents: 'none' }}>
            <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} className={classes.edge} />
        </g>
    );
};
