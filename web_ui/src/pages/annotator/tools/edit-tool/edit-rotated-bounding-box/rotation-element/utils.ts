// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RegionOfInterest } from '../../../../../../core/annotations/annotation.interface';
import { isPointWithinRoi } from '../../../geometry-utils';
import { SideAnchorLocationsProps } from '../location';

export enum Direction {
    N = 'N',
    W = 'W',
    S = 'S',
    E = 'E',
    MIDDLE = 'Middle',
}

export const getDirection = (sideAnchorLocations: SideAnchorLocationsProps, roi: RegionOfInterest): Direction => {
    const locations = sideAnchorLocations.withGap;

    if (isPointWithinRoi(roi, locations.N)) {
        return Direction.N;
    } else if (isPointWithinRoi(roi, locations.W)) {
        return Direction.W;
    } else if (isPointWithinRoi(roi, locations.S)) {
        return Direction.S;
    } else if (isPointWithinRoi(roi, locations.E)) {
        return Direction.E;
    } else {
        return Direction.MIDDLE;
    }
};
