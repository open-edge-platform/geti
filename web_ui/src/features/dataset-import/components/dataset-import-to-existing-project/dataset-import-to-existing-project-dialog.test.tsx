// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportToExistingProjectItem } from '../../../../core/datasets/dataset.interface';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { useDatasetImportToExistingProject } from '../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import {
    getMockedProject,
    mockedProjectContextProps,
} from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { projectListRender } from '../../../../test-utils/projects-list-providers-render';
import { DatasetImportToExistingProjectDialog } from './dataset-import-to-existing-project-dialog.component';

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

const mockDatasetImportDialogState = {
    isOpen: true,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

const mockDatasetImportDeleteDialogState = {
    isOpen: false,
    open: jest.fn(),
    toggle: jest.fn(),
    setOpen: jest.fn(),
    close: jest.fn(),
};

jest.mock('../../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../../notification/notification.component'),
    useNotification: () => ({ addNotification: jest.fn() }),
}));

jest.mock('../../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({
        project: {
            domains: [],
            tasks: [],
        },
        isSingleDomainProject: jest.fn(),
    })),
}));

jest.mock(
    '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component',
    () => ({
        ...jest.requireActual(
            '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
        ),
        useDatasetImportToExistingProject: jest.fn(() => ({
            isReady: () => jest.fn(),
        })),
    })
);

const renderMockedComponent = async (options?: Parameters<typeof projectListRender>[1]) => {
    return projectListRender(
        <DatasetImportToExistingProjectDialog
            datasetImportDialogState={mockDatasetImportDialogState}
            datasetImportDeleteDialogState={mockDatasetImportDeleteDialogState}
        />,
        options
    );
};

describe(DatasetImportToExistingProjectDialog, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('dialog dismiss', async () => {
        const mockedSetActiveDatasetImportId = jest.fn();
        jest.mocked(useDatasetImportToExistingProject).mockReturnValue({
            ...jest.requireActual(
                '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
            ),
            isReady: jest.fn(),
            setActiveDatasetImportId: mockedSetActiveDatasetImportId,
        });

        await renderMockedComponent();

        fireEvent.click(screen.getByRole('button', { name: /hide/i }));

        expect(mockDatasetImportDialogState.close).toHaveBeenCalled();
        expect(mockedSetActiveDatasetImportId).toHaveBeenCalledWith(undefined);
    });

    it('should render DatasetImportDnd component when there is no activeDatasetImportItem', async () => {
        await renderMockedComponent();
        expect(screen.getByRole('heading')).toHaveTextContent('Import dataset');
        expect(screen.getByLabelText('dataset-import-dnd')).toBeVisible();
    });

    it.each([
        { status: DATASET_IMPORT_STATUSES.UPLOADING },
        { status: DATASET_IMPORT_STATUSES.PREPARING },
        { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
        { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
    ])(
        'should render DatasetImportProgress component when activeDatasetImportItem is exist and have "$status" status',
        async ({ status }) => {
            jest.mocked(useDatasetImportToExistingProject).mockReturnValue({
                ...jest.requireActual(
                    '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
                ),
                isReady: jest.fn(),
                activeDatasetImport: { ...mockDatasetImportItem, status },
            });

            await renderMockedComponent();

            expect(screen.getByRole('heading')).toHaveTextContent('Import dataset');
            expect(screen.getByLabelText('dataset-import-progress')).toBeVisible();
        }
    );

    it.each([
        { status: DATASET_IMPORT_STATUSES.READY },
        { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
    ])(
        'should render DatasetImportToExistingProjectMapLabels component when activeDatasetImportItem is exist and have "$status" status',
        async ({ status }) => {
            jest.mocked(useDatasetImportToExistingProject).mockReturnValue({
                ...jest.requireActual(
                    '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
                ),
                isReady: jest.fn(),
                activeDatasetImport: { ...mockDatasetImportItem, labels: ['a', 'z'], status },
            });

            jest.mocked(useProject).mockImplementation(() =>
                mockedProjectContextProps({ project: getMockedProject({ tasks: [getMockedTask({ labels: [] })] }) })
            );

            await renderMockedComponent();

            expect(screen.getByRole('heading')).toHaveTextContent('Import dataset');
            expect(screen.getByLabelText('dataset-import-to-existing-project-map-labels')).toBeVisible();
        }
    );

    it('Display proper information when there is no label to map in dataset importing', async () => {
        jest.mocked(useDatasetImportToExistingProject).mockReturnValue({
            ...jest.requireActual(
                '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
            ),
            isReady: jest.fn(),
            activeDatasetImport: {
                ...mockDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            },
        });

        await renderMockedComponent();
        expect(
            screen.getByText('No labels were detected in the dataset. Only images will be imported.')
        ).toBeInTheDocument();
    });

    it('call import job', async () => {
        const mockedImportDatasetJob = jest.fn();
        jest.mocked(useDatasetImportToExistingProject).mockReturnValue({
            ...jest.requireActual(
                '../../../../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component'
            ),
            isReady: jest.fn(() => true),
            importDataset: jest.fn(),
            importDatasetJob: mockedImportDatasetJob,
            setActiveDatasetImportId: jest.fn(),
            activeDatasetImport: {
                ...mockDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            },
        });

        await renderMockedComponent();

        fireEvent.click(screen.getByRole('button', { name: /import/i }));

        expect(mockedImportDatasetJob).toHaveBeenCalledWith(mockDatasetImportItem.id);
    });
});
