// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportToExistingProjectItem } from '../../../../core/datasets/dataset.interface';
import { Label } from '../../../../core/labels/label.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { DatasetImportToExistingProjectMapLabels } from './dataset-import-to-existing-project-map-labels.component';

const mockDatasetImportItem: DatasetImportToExistingProjectItem = {
    id: '987-654-321',
    name: 'Test Dataset',
    size: '1Gb',
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    progress: 50,
    startAt: 0,
    startFromBytes: 0,
    uploadId: '192-837-465',
    bytesRemaining: '500Mb',
    timeRemaining: '10 minutes',
    warnings: [],
    labels: [],
    labelsMap: {},
    projectId: '',
    datasetId: '',
    datasetName: '',
};

const mockProjectLabels: Label[] = [
    getMockedLabel({ id: '1', name: 'Felinology', color: 'red', group: 'default' }),
    getMockedLabel({ id: '2', name: 'Kinology', color: 'blue', group: 'default' }),
];

const mockPatchActiveDatasetImport = jest.fn();
jest.mock(
    '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component',
    () => ({
        ...jest.requireActual(
            '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
        ),
        useDatasetImportToExistingProject: jest.fn(() => ({ patchActiveDatasetImport: mockPatchActiveDatasetImport })),
    })
);

describe(DatasetImportToExistingProjectMapLabels, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should properly render initiated component', () => {
        render(
            <DatasetImportToExistingProjectMapLabels
                projectLabels={mockProjectLabels}
                activeDatasetImport={{ ...mockDatasetImportItem, labels: ['cat', 'dog'] }}
            />
        );

        expect(screen.getByText('Existing labels')).toBeVisible();
        expect(screen.getByText('Target labels')).toBeVisible();

        expect(screen.getByText('cat')).toBeVisible();
        expect(screen.getByText('dog')).toBeVisible();

        expect(screen.getAllByText('→')).toHaveLength(2);
        expect(screen.getAllByRole('textbox', { name: 'Select label' })).toHaveLength(2);

        expect(screen.queryAllByLabelText('clear-mapping-button')).toHaveLength(0);
    });

    it('should properly interact on labels mapping change', async () => {
        render(
            <DatasetImportToExistingProjectMapLabels
                projectLabels={mockProjectLabels}
                activeDatasetImport={{ ...mockDatasetImportItem, labels: ['cat'] }}
            />
        );

        expect(screen.getByRole('textbox', { name: 'Select label' })).toBeVisible();
        await userEvent.type(screen.getByRole('textbox', { name: 'Select label' }), 'nology');

        expect(screen.getAllByRole('listitem', { hidden: true })).toHaveLength(2);
        expect(screen.getAllByRole('listitem')[0]).toHaveTextContent('Felinology');
        expect(screen.getAllByRole('listitem')[1]).toHaveTextContent('Kinology');

        fireEvent.click(screen.getAllByRole('listitem')[0]);
        expect(mockPatchActiveDatasetImport).toHaveBeenCalledWith({ labelsMap: { cat: '1' } });

        await userEvent.type(screen.getByRole('textbox', { name: 'Select label' }), 'nology');
        fireEvent.click(screen.getAllByRole('listitem')[1]);
        expect(mockPatchActiveDatasetImport).toHaveBeenCalledWith({ labelsMap: { cat: '2' } });
    });

    it('should allow clearing labels mapping', () => {
        render(
            <DatasetImportToExistingProjectMapLabels
                projectLabels={mockProjectLabels}
                activeDatasetImport={{
                    ...mockDatasetImportItem,
                    labels: ['cat'],
                    labelsMap: { ['cat']: mockProjectLabels[0].id },
                }}
            />
        );

        fireEvent.click(screen.getByLabelText('clear-mapping-button'));
        expect(mockPatchActiveDatasetImport).toHaveBeenCalledWith({ labelsMap: {} });
    });

    it('labels should be sorted alphabetically', () => {
        render(
            <DatasetImportToExistingProjectMapLabels
                projectLabels={mockProjectLabels}
                activeDatasetImport={{
                    ...mockDatasetImportItem,
                    labels: ['zebra', 'cat', 'fish'],
                    labelsMap: {},
                }}
            />
        );

        expect(screen.getByTestId('label-mapping-0')).toHaveTextContent('cat');
        expect(screen.getByTestId('label-mapping-1')).toHaveTextContent('fish');
        expect(screen.getByTestId('label-mapping-2')).toHaveTextContent('zebra');
    });

    it("labels should be mapped automatically when they are the same like project's labels", () => {
        const projectLabels = [
            getMockedLabel({ id: '1', name: 'zebra', color: 'red', group: 'default' }),
            getMockedLabel({ id: '2', name: 'cat', color: 'blue', group: 'default' }),
            getMockedLabel({ id: '3', name: 'fish', color: 'yellow', group: 'default' }),
        ];

        const labelsMap = {
            zebra: '1',
            cat: '2',
            fish: '3',
        };

        const labels = ['zebra', 'cat', 'fish'];

        render(
            <DatasetImportToExistingProjectMapLabels
                projectLabels={projectLabels}
                activeDatasetImport={{
                    ...mockDatasetImportItem,
                    labels,
                    labelsMap,
                }}
            />
        );

        labels.forEach((labelName) => {
            expect(screen.getByTestId(idMatchingFormat(`existing-label-${labelName}-id`))).toBeInTheDocument();
            expect(screen.getByTestId(idMatchingFormat(`target-label-${labelName}-id`))).toBeInTheDocument();
        });
    });
});
