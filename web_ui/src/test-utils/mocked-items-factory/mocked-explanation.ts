// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Explanation } from '../../core/annotations/prediction.interface';

export const getMockedExplanation = (explanationOptions: Partial<Explanation> = {}): Explanation => {
    return {
        labelsId: '321',
        id: '123',
        url: 'url-test',
        name: 'name-test',
        roi: {
            id: 'roi-id',
            shape: {
                y: 0,
                x: 0,
                type: 'rectangle',
                height: 10,
                width: 10,
            },
        },
        ...explanationOptions,
    };
};
