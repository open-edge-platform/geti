// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { render, screen } from '@testing-library/react';

import { Label } from '../../../../core/labels/label.interface';
import { getMockedKeypointNode } from '../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { NodeLabel } from './node-label.component';

describe('NodeLabel', () => {
    it('render the label name if not a prediction', () => {
        const labelName = 'Test Label';
        const mockPoint = getMockedKeypointNode({ label: getMockedLabel({ name: labelName }) });

        render(<NodeLabel point={mockPoint} />);

        expect(screen.getByText(labelName)).toBeVisible();
        expect(screen.queryByLabelText('prediction icon')).not.toBeInTheDocument();
    });

    it('render the prediction label with score if it is a prediction', () => {
        const labelName = 'Prediction Label';
        const mockPredictionPoint = getMockedKeypointNode({
            label: { ...getMockedLabel({ name: labelName }), score: 0.5, source: { userId: undefined } } as Label,
        });

        render(<NodeLabel point={mockPredictionPoint} />);

        expect(screen.getByText('(50%)')).toBeVisible();
        expect(screen.getByText(labelName)).toBeVisible();
        expect(screen.getByLabelText('prediction icon')).toBeVisible();
    });
});
