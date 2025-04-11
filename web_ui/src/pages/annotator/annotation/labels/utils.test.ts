// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { labelFromUser } from './../../../../core/annotations/utils';
import { getMockedLabel } from './../../../../test-utils/mocked-items-factory/mocked-labels';
import { getLabelsColor } from './utils';

describe('Annotation label utils', () => {
    it('getLabelsColor', () => {
        const mockUserId = 'some-id';
        const mockLabels = [
            labelFromUser(getMockedLabel({ id: '1', color: 'blue' }), mockUserId),
            labelFromUser(getMockedLabel({ id: '2', color: 'red' }), mockUserId),
        ];
        const mockTask = getMockedTask({
            labels: [getMockedLabel({ id: '1', color: 'blue' })],
        });

        // Without a selected task
        expect(getLabelsColor(mockLabels, null)).toEqual('red');

        // With a selected task
        expect(getLabelsColor(mockLabels, mockTask)).toEqual('blue');
    });
});
