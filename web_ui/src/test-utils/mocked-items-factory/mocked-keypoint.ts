// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeypointNode } from '../../core/annotations/shapes.interface';
import { getMockedLabel } from './mocked-labels';

export const getMockedKeypointNode = (point?: Partial<KeypointNode>): KeypointNode => {
    return {
        x: 0,
        y: 0,
        isVisible: true,
        label: getMockedLabel({ color: '#000000' }),
        ...point,
    };
};
