// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DatasetImportLabel, DatasetImportToNewProjectItem } from '../../../../../core/datasets/dataset.interface';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { DatasetImportToNewProjectLabels } from './dataset-import-to-new-project-labels.component';

const MOCKED_LABELS_FLAT: DatasetImportLabel[] = [{ name: 'cat' }, { name: 'dog' }];

const MOCKED_LABELS_HIERARCHY: DatasetImportLabel[] = [
    { name: 'animal' },
    { name: 'cat', group: 'pets', parent: 'animal' },
    { name: 'dog', group: 'pets', parent: 'animal' },
    { name: 'rat', group: 'wild', parent: 'animal' },
    { name: 'fox', group: 'wild', parent: 'animal' },
];

const MOCKED_LABELS_DEEP_HIERARCHY: DatasetImportLabel[] = [
    { name: 'Guitars' },

    { name: 'Single Cut', group: 'Electric', parent: 'Guitars' },
    { name: 'PRS Custom 22', group: 'PRS', parent: 'Single Cut' },
    { name: 'PRS Custom 24', group: 'PRS', parent: 'Single Cut' },
    { name: 'Gibson Les Paul Traditional', group: 'Gibson', parent: 'Single Cut' },
    { name: 'Gibson Les Paul Studio', group: 'Gibson', parent: 'Single Cut' },
    { name: 'Gibson Les Paul Tribute', group: 'Gibson', parent: 'Single Cut' },
    { name: 'Fender Telecaster Nashville', group: 'Fender', parent: 'Single Cut' },
    { name: 'Fender Jazzmaster', group: 'Fender', parent: 'Single Cut' },

    { name: 'Double Cut', group: 'Electric', parent: 'Guitars' },
    { name: 'Fender Stratocaster Player', group: 'Fender', parent: 'Double Cut' },
    { name: 'Ibanez RG', group: 'Ibanez', parent: 'Double Cut' },
    { name: 'Ibanez AZ', group: 'Ibanez', parent: 'Double Cut' },
    { name: 'Ibanez RG421-AHM', parent: 'Ibanez RG' },
    { name: 'Ibanez AZ2204-ICM', parent: 'Ibanez AZ' },

    { name: 'Hollow', group: 'Acoustic', parent: 'Guitars' },
    { name: 'PRS SE Hollowbody', group: 'PRS', parent: 'Hollow' },
];

const mockedAddNotifications = jest.fn();
jest.mock('../../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../../notification/notification.component'),
    useNotification: jest.fn(() => ({
        addNotification: mockedAddNotifications,
    })),
}));

describe('DatasetImportToNewProjectLabels', () => {
    const mockPatchUpload = jest.fn();

    const mockDatasetImportItem = {
        id: 'testId',
        name: 'testName',
        labels: [],
        labelsToSelect: [],
        firstChainLabels: [],
    } as unknown as DatasetImportToNewProjectItem;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should show "No labels" and display a warning notification when dataset has no labels to select', () => {
        const mockUploadEmptyItem = {
            name: 'fileTestName',
            labels: [],
            firstChainLabels: [],
            labelsToSelect: [],
        } as unknown as DatasetImportToNewProjectItem;

        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={mockUploadEmptyItem}
                patchDatasetImport={mockPatchUpload}
            />
        );

        expect(screen.getByText('No labels')).toBeInTheDocument();
    });

    it('should correctly display the dataset with a "flat" labels structure', () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_FLAT }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        expect(mockedAddNotifications).not.toHaveBeenCalled();
        expect(screen.queryByText('No labels')).not.toBeInTheDocument();

        expect(screen.queryAllByTestId(/expand-collapse-button/)).toHaveLength(0);
    });

    it('should not display checkboxes when hasCheckbox is set to false', () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={false}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_FLAT }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        expect(screen.queryByRole('checkbox', { name: 'select-all-labels' })).not.toBeInTheDocument();
    });

    it('should correctly display the dataset with a "hierarchical" labels structure', () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_HIERARCHY }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        expect(mockedAddNotifications).not.toHaveBeenCalled();
        expect(screen.queryByText('No labels')).not.toBeInTheDocument();

        const expandCollapseButtons = screen.queryAllByTestId(/expand-collapse-button/);

        // 3 buttons expected: for animal parent label and for 2 groups - pets and wild
        expect(expandCollapseButtons).toHaveLength(3);

        for (const button of expandCollapseButtons) {
            expect(button).toHaveAttribute('aria-expanded');
        }
    });

    it('should correctly display the dataset with a "hierarchical" labels structure which is collapsed by default', () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_HIERARCHY }}
                patchDatasetImport={mockPatchUpload}
                labelsInitiallyCollapsed={true}
            />
        );

        expect(mockedAddNotifications).not.toHaveBeenCalled();
        expect(screen.queryByText('No labels')).not.toBeInTheDocument();

        const expandCollapseButtons = screen.queryAllByTestId(/expand-collapse-button/);

        // 3 buttons expected: for animal parent label and for 2 groups - pets and wild
        expect(expandCollapseButtons).toHaveLength(3);

        for (const button of expandCollapseButtons) {
            expect(button).not.toHaveAttribute('aria-expanded', 'true');
        }
    });

    it('should correctly behave on toggle expand/collapse button', async () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_HIERARCHY }}
                patchDatasetImport={mockPatchUpload}
                labelsInitiallyCollapsed={true}
            />
        );

        expect(mockedAddNotifications).not.toHaveBeenCalled();
        expect(screen.queryByText('No labels')).not.toBeInTheDocument();

        expect(screen.getByTestId('treeitem-group-animal')).not.toBeVisible();
        expect(screen.getByTestId('treeitem-group-pets')).not.toBeVisible();
        expect(screen.getByTestId('treeitem-group-wild')).not.toBeVisible();

        const expandCollapseButtons = screen.queryAllByTestId(/expand-collapse-button/);

        await userEvent.click(expandCollapseButtons[0]);
        expect(screen.getByTestId('treeitem-group-animal')).toBeVisible();

        await userEvent.click(expandCollapseButtons[1]);
        expect(screen.getByTestId('treeitem-group-pets')).toBeVisible();

        await userEvent.click(expandCollapseButtons[2]);
        expect(screen.getByTestId('treeitem-group-wild')).toBeVisible();

        await userEvent.click(expandCollapseButtons[2]);
        expect(screen.getByTestId('treeitem-group-wild')).not.toBeVisible();
        expect(screen.getByTestId('treeitem-group-pets')).toBeVisible();
        expect(screen.getByTestId('treeitem-group-animal')).toBeVisible();

        await userEvent.click(expandCollapseButtons[0]);
        expect(screen.getByTestId('treeitem-group-animal')).not.toBeVisible();
        expect(screen.getByTestId('treeitem-group-pets')).not.toBeVisible();
        expect(screen.getByTestId('treeitem-group-wild')).not.toBeVisible();
    });

    it('should properly behave on change label color button click', async () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{
                    ...mockDatasetImportItem,
                    labelsToSelect: MOCKED_LABELS_FLAT,
                    labelColorMap: { cat: '#FF0000', dog: '#00FF00' },
                }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        const changeColorButtons = screen.getAllByTestId(/change-color-button/);

        // 2 buttons expected for each "flat" label
        expect(changeColorButtons).toHaveLength(2);

        // Open the first label's color picker
        await userEvent.click(screen.getByTestId('change-color-button-cat-button'));

        expect(screen.getByRole('slider', { name: 'Color' })).toBeInTheDocument();
        expect(screen.getByRole('slider', { name: 'Hue' })).toBeInTheDocument();

        const newColor = 'FEFEFE';
        const colorInput = screen.getByTestId('change-color-button-cat-color-input');

        await userEvent.clear(colorInput);
        await userEvent.type(colorInput, newColor);

        await userEvent.click(screen.getByRole('button', { name: /confirm/i }));

        expect(mockPatchUpload).toHaveBeenCalledWith({
            id: mockDatasetImportItem.id,
            labelColorMap: { cat: `#${newColor}`, dog: '#00FF00' },
        });
    });

    it('should properly behave on "select all" user action', async () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_HIERARCHY }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        await userEvent.click(screen.getByLabelText('select-all-labels'));
        expect(mockPatchUpload).toHaveBeenCalledWith({ id: mockDatasetImportItem.id, labels: MOCKED_LABELS_HIERARCHY });
    });

    it('should not add duplicate labels on toggling selection checkbox', async () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_FLAT }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        await userEvent.click(screen.getByLabelText('select-cat-label'));
        await userEvent.click(screen.getByLabelText('select-cat-label'));
        await userEvent.click(screen.getByLabelText('select-cat-label'));

        expect(mockPatchUpload).toHaveBeenCalledWith({ id: mockDatasetImportItem.id, labels: [{ name: 'cat' }] });
    });

    it('should select all children labels on root level parent label select', async () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_DEEP_HIERARCHY }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        await userEvent.click(screen.getByLabelText('select-guitars-label'));
        expect(mockPatchUpload).toHaveBeenCalledWith({
            id: mockDatasetImportItem.id,
            labels: expect.arrayContaining(MOCKED_LABELS_DEEP_HIERARCHY),
        });
    });

    it('should select only the level children and parent labels on level parent label select', async () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_DEEP_HIERARCHY }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        await userEvent.click(screen.getByLabelText('select-double-cut-label'));
        expect(mockPatchUpload).toHaveBeenCalledWith({
            id: mockDatasetImportItem.id,
            labels: expect.arrayContaining([
                { name: 'Guitars' },
                { name: 'Double Cut', group: 'Electric', parent: 'Guitars' },
                { name: 'Fender Stratocaster Player', group: 'Fender', parent: 'Double Cut' },
                { name: 'Ibanez RG', group: 'Ibanez', parent: 'Double Cut' },
                { name: 'Ibanez AZ', group: 'Ibanez', parent: 'Double Cut' },
                { name: 'Ibanez RG421-AHM', parent: 'Ibanez RG' },
                { name: 'Ibanez AZ2204-ICM', parent: 'Ibanez AZ' },
            ]),
        });
    });

    it('should unselect only self label after it was selected by parent', async () => {
        render(
            <DatasetImportToNewProjectLabels
                hasCheckbox={true}
                datasetImportItem={{ ...mockDatasetImportItem, labelsToSelect: MOCKED_LABELS_DEEP_HIERARCHY }}
                patchDatasetImport={mockPatchUpload}
            />
        );

        await userEvent.click(screen.getByLabelText('select-double-cut-label'));

        await userEvent.click(screen.getByLabelText('select-ibanez-az2204-icm-label'));
        expect(mockPatchUpload).toHaveBeenCalledWith({
            id: mockDatasetImportItem.id,
            labels: expect.arrayContaining([
                { name: 'Guitars' },
                { name: 'Double Cut', group: 'Electric', parent: 'Guitars' },
                { name: 'Fender Stratocaster Player', group: 'Fender', parent: 'Double Cut' },
                { name: 'Ibanez RG', group: 'Ibanez', parent: 'Double Cut' },
                { name: 'Ibanez AZ', group: 'Ibanez', parent: 'Double Cut' },
                { name: 'Ibanez RG421-AHM', parent: 'Ibanez RG' },
            ]),
        });

        await userEvent.click(screen.getByLabelText('select-ibanez-rg421-ahm-label'));
        expect(mockPatchUpload).toHaveBeenCalledWith({
            id: mockDatasetImportItem.id,
            labels: expect.arrayContaining([
                { name: 'Guitars' },
                { name: 'Double Cut', group: 'Electric', parent: 'Guitars' },
                { name: 'Fender Stratocaster Player', group: 'Fender', parent: 'Double Cut' },
                { name: 'Ibanez RG', group: 'Ibanez', parent: 'Double Cut' },
                { name: 'Ibanez AZ', group: 'Ibanez', parent: 'Double Cut' },
            ]),
        });

        await userEvent.click(screen.getByLabelText('select-ibanez-az-label'));
        await userEvent.click(screen.getByLabelText('select-ibanez-rg-label'));
        expect(mockPatchUpload).toHaveBeenCalledWith({
            id: mockDatasetImportItem.id,
            labels: expect.arrayContaining([
                { name: 'Guitars' },
                { name: 'Double Cut', group: 'Electric', parent: 'Guitars' },
                { name: 'Fender Stratocaster Player', group: 'Fender', parent: 'Double Cut' },
            ]),
        });
    });
});
