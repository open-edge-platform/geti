// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Shape } from '../../../../../core/annotations/shapes.interface';

export interface SegmentAnythingResult {
    shapes: Shape[];
    areas: number[];
    maxContourIdx: number;
}
