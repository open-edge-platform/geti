// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { KeypointErrorMessage, KeypointErrorProps } from './keypoint-error-message.component';
import { KEYPOINT_DUPLICATED_LABELS, KEYPOINT_MISSING_LABELS } from './utils';

describe('KeypointErrorMessage', () => {
    const renderApp = ({ labels = [], labelsMap = {} }: Partial<KeypointErrorProps>) => {
        return render(<KeypointErrorMessage labels={labels} labelsMap={labelsMap} />);
    };
    it('render empty if not errors are present', () => {
        const { container } = renderApp({});

        expect(container).toBeEmptyDOMElement();
    });

    it('show missing labels message when labels are not in labelsMap', () => {
        const mockLabelsMap = { key1: 'label3' };
        const mockLabels = [
            getMockedLabel({ id: 'label1', name: 'Label 1' }),
            getMockedLabel({ id: 'label2', name: 'Label 2' }),
        ];

        renderApp({ labels: mockLabels, labelsMap: mockLabelsMap });

        expect(screen.getByText(`${KEYPOINT_MISSING_LABELS} Label 1, Label 2`)).toBeVisible();
    });

    it('show duplicated labels message when labels are duplicated', () => {
        const mockLabels = [
            getMockedLabel({ id: 'label1', name: 'Label 1' }),
            getMockedLabel({ id: 'label2', name: 'Label 2' }),
        ];
        const mockLabelsMap = { key1: 'label1', key2: 'label1', key3: 'label2', key4: 'label2' };

        renderApp({ labels: mockLabels, labelsMap: mockLabelsMap });
        expect(screen.getByText(`${KEYPOINT_DUPLICATED_LABELS} Label 1, Label 2`)).toBeVisible();
    });

    it('show both error messages when both conditions are met', () => {
        const mockLabels = [
            getMockedLabel({ id: 'label1', name: 'Label 1' }),
            getMockedLabel({ id: 'label2', name: 'Label 2' }),
            getMockedLabel({ id: 'label3', name: 'Label 3' }),
        ];
        const mockLabelsMap = { key1: 'label1', key2: 'label1' };

        renderApp({ labels: mockLabels, labelsMap: mockLabelsMap });

        expect(screen.getByText(`${KEYPOINT_DUPLICATED_LABELS} Label 1`)).toBeVisible();
        expect(screen.getByText(`${KEYPOINT_MISSING_LABELS} Label 2, Label 3`)).toBeVisible();
    });
});
