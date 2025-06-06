// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import {
    DATASET_IMPORT_STATUSES,
    DATASET_IMPORT_TASK_TYPE,
    DATASET_IMPORT_TO_NEW_PROJECT_STEP,
} from '../../../../../core/datasets/dataset.enum';
import { DatasetImportToNewProjectItem, DatasetImportWarning } from '../../../../../core/datasets/dataset.interface';
import { getMockedSupportedProjectTypes } from '../../../../../test-utils/mocked-items-factory/mocked-dataset-import';
import { getMockedProjectIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../../project-details/providers/project-provider/project-provider.component';
import { DatasetImportToNewProjectDialogContent } from './dataset-import-to-new-project-dialog-content.component';

const MOCKED_LABELS_FLAT = [{ name: 'cat' }, { name: 'dog' }];

const mockDatasetImportItem: DatasetImportToNewProjectItem = {
    id: '987-654-321',
    name: 'Test Dataset',
    size: '1Gb',
    preparingJobId: null,
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    progress: 50,
    startAt: 0,
    startFromBytes: 0,
    uploadId: '192-837-465',
    bytesRemaining: '500Mb',
    timeRemaining: '10 minutes',
    projectName: '',
    taskType: DATASET_IMPORT_TASK_TYPE.DETECTION,
    warnings: [],
    labels: [],
    firstChainTaskType: null,
    firstChainLabels: [],
    labelsToSelect: [],
    labelColorMap: {},
    supportedProjectTypes: [],
    activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
    openedSteps: [],
    completedSteps: [],
};

jest.mock('../../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../../notification/notification.component'),
    useNotification: () => ({ addNotification: jest.fn() }),
}));

const renderMockedComponent = async (datasetImportItem?: DatasetImportToNewProjectItem) => {
    render(
        <ProjectProvider
            projectIdentifier={getMockedProjectIdentifier({
                projectId: 'project-id',
                workspaceId: 'workspace-id',
            })}
        >
            <DatasetImportToNewProjectDialogContent
                datasetImportItem={datasetImportItem}
                prepareDataset={jest.fn()}
                patchDatasetImport={jest.fn()}
                setActiveDatasetImportId={jest.fn()}
                anomalyRevamp={false}
            />
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
};
describe(DatasetImportToNewProjectDialogContent, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should render DatasetImportDnd component when there is no datasetImportItem', async () => {
        await renderMockedComponent();
        expect(screen.getByLabelText('dataset-import-dnd')).toBeVisible();
    });

    it('should render DatasetImportProgress component when the datasetImportItem is exist, active step is "dataset" and there is no warnings', async () => {
        await renderMockedComponent({
            ...mockDatasetImportItem,
            activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
        });
        expect(screen.getByLabelText('dataset-import-progress')).toBeVisible();
    });

    it('should render DatasetImportWarnings component when the datasetImportItem is exist, active step is "dataset" and there are warnings', async () => {
        await renderMockedComponent({
            ...mockDatasetImportItem,
            warnings: [{} as DatasetImportWarning],
            activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET,
        });
        expect(screen.getByLabelText('dataset-import-warnings')).toBeVisible();
    });

    it('should render DatasetImportToNewProjectDomain component when datasetImportItem exists, active step is "domain"', async () => {
        await renderMockedComponent({
            ...mockDatasetImportItem,
            activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN,
        });
        expect(screen.getByLabelText('dataset-import-to-new-project-domain')).toBeVisible();
    });

    describe('DatasetImportToNewProjectLabels', () => {
        it('datasetImportItem exists, active step is "labels"', async () => {
            await renderMockedComponent({
                ...mockDatasetImportItem,
                labelsToSelect: MOCKED_LABELS_FLAT,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
            });
            expect(screen.getByLabelText('dataset-import-to-new-project-labels')).toBeVisible();
            expect(screen.queryByRole('checkbox', { name: 'select-all-labels' })).toBeInTheDocument();
        });

        it('not render select label for keypoint detection', async () => {
            const supportedProjectTypes = getMockedSupportedProjectTypes([
                {
                    projectType: DATASET_IMPORT_TASK_TYPE.KEYPOINT_DETECTION,
                    pipeline: {
                        connections: [],
                        tasks: [
                            {
                                title: 'keypoint detection',
                                labels: MOCKED_LABELS_FLAT,
                                keypointStructure: { edges: [], positions: [] },
                                taskType: DATASET_IMPORT_TASK_TYPE.KEYPOINT_DETECTION,
                            },
                        ],
                    },
                },
            ]);

            await renderMockedComponent({
                ...mockDatasetImportItem,
                labelsToSelect: MOCKED_LABELS_FLAT,
                supportedProjectTypes,
                activeStep: DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS,
            });
            expect(screen.getByLabelText('dataset-import-to-new-project-labels')).toBeVisible();
            expect(screen.queryByRole('checkbox', { name: 'select-all-labels' })).not.toBeInTheDocument();
        });
    });
});
