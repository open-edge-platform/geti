// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
