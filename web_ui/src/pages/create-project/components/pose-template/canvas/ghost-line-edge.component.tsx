// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
