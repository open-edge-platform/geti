// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Point } from '../../../../core/annotations/shapes.interface';
import { CROSSHAIR_LINE_DIRECTION, CrosshairLine } from './crosshair-line.component';

interface CrosshairProps {
    location: Point | null;
    zoom: number;
}

export const Crosshair = ({ location, zoom }: CrosshairProps): JSX.Element => {
    if (location === null) {
        return <g></g>;
    }

    return (
        <g>
            <CrosshairLine zoom={zoom} point={location} direction={CROSSHAIR_LINE_DIRECTION.HORIZONTAL} />
            <CrosshairLine zoom={zoom} point={location} direction={CROSSHAIR_LINE_DIRECTION.VERTICAL} />
        </g>
    );
};
