// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { LabelsRelationType } from '../../../core/labels/label.interface';
import { DOMAIN } from '../../../core/projects/core.interface';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { TaskLabelTreeContainer } from './task-label-tree-container.component';

const getMockedLabelsTree = (relation: LabelsRelationType) =>
    getMockedTreeGroup({
        name: 'Animal',
        relation,
        children: [
            getMockedTreeLabel({ name: 'Cat', relation }),
            getMockedTreeLabel({
                name: 'Dog',
                relation,
                children: [
                    getMockedTreeGroup({
                        name: 'Color',
                        relation,
                        children: [
                            getMockedTreeLabel({ name: 'White', relation }),
                            getMockedTreeLabel({ name: 'Black', relation }),
                            getMockedTreeLabel({ name: 'Mixed', relation }),
                        ],
                    }),
                ],
            }),
            getMockedTreeLabel({ name: 'Hamster', relation }),
        ],
    });

describe('TaskLabelTreeContainer', () => {
    it('shows "No Results"', async () => {
        const mockOnClick = jest.fn();

        render(<TaskLabelTreeContainer tasksMetadata={[]} suffix={() => <></>} onClick={mockOnClick} />);

        expect(screen.getByText('No Results')).toBeVisible();
    });

    it('does not show domain (single project)', async () => {
        const mockOnClick = jest.fn();
        const taskMetadata = [
            {
                domain: DOMAIN.CLASSIFICATION,
                relation: LabelsRelationType.MULTI_SELECTION,
                labels: [getMockedLabelsTree(LabelsRelationType.MULTI_SELECTION)],
            },
        ];

        render(<TaskLabelTreeContainer tasksMetadata={taskMetadata} suffix={() => <></>} onClick={mockOnClick} />);

        expect(screen.queryByText(DOMAIN.CLASSIFICATION)).not.toBeInTheDocument();
    });

    it('shows labels domains (task-chain)', async () => {
        const mockOnClick = jest.fn();
        const taskMetadata = [
            {
                domain: DOMAIN.DETECTION,
                relation: LabelsRelationType.MULTI_SELECTION,
                labels: [getMockedLabelsTree(LabelsRelationType.MULTI_SELECTION)],
            },
            {
                domain: DOMAIN.CLASSIFICATION,
                relation: LabelsRelationType.MULTI_SELECTION,
                labels: [getMockedLabelsTree(LabelsRelationType.MULTI_SELECTION)],
            },
        ];

        render(<TaskLabelTreeContainer tasksMetadata={taskMetadata} suffix={() => <></>} onClick={mockOnClick} />);

        expect(screen.getByText(DOMAIN.DETECTION)).toBeVisible();
        expect(screen.getByText(DOMAIN.CLASSIFICATION)).toBeVisible();
    });
});
