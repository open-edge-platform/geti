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
