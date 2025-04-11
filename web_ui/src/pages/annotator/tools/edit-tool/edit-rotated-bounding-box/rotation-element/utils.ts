// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { RegionOfInterest } from '../../../../../../core/annotations/annotation.interface';
import { isPointWithinRoi } from '../../../utils';
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
