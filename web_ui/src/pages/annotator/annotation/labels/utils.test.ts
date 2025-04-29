// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
