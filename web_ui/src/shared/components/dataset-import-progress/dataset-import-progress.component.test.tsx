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

import { screen, waitFor } from '@testing-library/react';

import { DATASET_IMPORT_DESCRIPTION, DATASET_IMPORT_HEADER } from '../../../core/datasets/dataset.const';
import { DATASET_IMPORT_STATUSES } from '../../../core/datasets/dataset.enum';
import { DatasetImportItem } from '../../../core/datasets/dataset.interface';
import { createInMemoryDatasetImportService } from '../../../core/datasets/services/in-memory-dataset-import-service';
import { JobState, JobStepState } from '../../../core/jobs/jobs.const';
import { JobPrepareDatasetImportNewProjectStatus } from '../../../core/jobs/jobs.interface';
import { getMockedPrepareJob } from '../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender } from '../../../test-utils/required-providers-render';
import { DatasetImportProgress } from './dataset-import-progress.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace_1',
    }),
}));

const mockDatasetImportItem: DatasetImportItem = {
    id: '987-654-321',
    name: 'Test Dataset',
    size: '1Gb',
    status: DATASET_IMPORT_STATUSES.UPLOADING,
    progress: 50,
    startAt: 0,
    startFromBytes: 0,
    uploadId: '192-837-465',
    bytesRemaining: '500Mb',
    timeRemaining: 'a few seconds left',
    warnings: [],
};

describe(DatasetImportProgress, () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const renderApp = async (
        datasetImportItem = mockDatasetImportItem,
        datasetImportService = createInMemoryDatasetImportService()
    ) => {
        providersRender(<DatasetImportProgress progressItem={{ ...datasetImportItem }} />, {
            services: { datasetImportService },
        });
    };

    describe('preparing status', () => {
        it('LoadingIndicator is visible if progress is equal to "0"', async () => {
            await renderApp({
                ...mockDatasetImportItem,
                status: DATASET_IMPORT_STATUSES.PREPARING,
                preparingJobId: '123',
            });

            expect(screen.queryByLabelText('Loading...')).toBeVisible();
            expect(screen.queryByAltText('progress-circular-loader')).not.toBeInTheDocument();

            expect(screen.getByText(String(DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.PREPARING]))).toBeVisible();
            expect(screen.getByText(/preparing.../i)).toBeVisible();

            expect(screen.getByText('Test Dataset')).toBeVisible();
            expect(screen.getByText('a few seconds left')).toBeVisible();
        });

        it('job step details are visible', async () => {
            const mockedStep = {
                index: 1,
                progress: 10,
                message: 'mocked step message',
                state: JobStepState.RUNNING,
                stepName: 'Test step',
            };
            const mockedDatasetImportService = createInMemoryDatasetImportService();
            mockedDatasetImportService.prepareDatasetImportNewProjectJob = async () => {
                return getMockedPrepareJob({
                    state: JobState.RUNNING,
                    steps: [mockedStep],
                }) as JobPrepareDatasetImportNewProjectStatus;
            };

            await renderApp(
                {
                    ...mockDatasetImportItem,
                    status: DATASET_IMPORT_STATUSES.PREPARING,
                    preparingJobId: '123',
                },
                mockedDatasetImportService
            );

            await waitFor(() => {
                expect(screen.queryByText(`${mockedStep.stepName}: ${mockedStep.message}`)).toBeVisible();
                expect(screen.getByText(`${mockedStep.progress}%`)).toBeVisible();
            });
        });
    });

    it.each([
        {
            status: DATASET_IMPORT_STATUSES.UPLOADING,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.UPLOADING],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.UPLOADING],
        },
        {
            status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.IMPORTING_ERROR],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.IMPORTING_ERROR],
        },
        {
            status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED],
        },
        {
            status: DATASET_IMPORT_STATUSES.PREPARING_ERROR,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.PREPARING_ERROR],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.PREPARING_ERROR],
        },
        {
            status: DATASET_IMPORT_STATUSES.READY,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.READY],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.READY],
        },
        {
            status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT],
        },
        {
            status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT],
        },
        {
            status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT],
        },
        {
            status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR],
        },
        {
            status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT],
        },
        {
            status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT],
        },
        {
            status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
            header: DATASET_IMPORT_HEADER[DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR],
            description: DATASET_IMPORT_DESCRIPTION[DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR],
        },
    ])(
        'should render "CircularLoader", "$header", "$description", "Test Dataset" and "a few seconds left" when datasetImportItem status is "$status"',
        async ({ status, header, description }) => {
            await renderApp({ ...mockDatasetImportItem, status });

            expect(screen.getByLabelText('progress-circular-loader')).toBeVisible();

            expect(screen.getByText(String(header))).toBeVisible();
            expect(screen.getByText(String(description))).toBeVisible();

            expect(screen.getByText('Test Dataset')).toBeVisible();
            expect(screen.getByText('a few seconds left')).toBeVisible();
        }
    );
    it.each([
        { status: DATASET_IMPORT_STATUSES.UPLOADING },
        { status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED },
        { status: DATASET_IMPORT_STATUSES.READY },
        { status: DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT },
        { status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT },
        { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT },
        { status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT },
        { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT },
    ])(
        'should render "CircularLoader" and "50%" inside it when datasetImportItem status is "$status"',
        async ({ status }) => {
            await renderApp({ ...mockDatasetImportItem, status });
            expect(screen.getByLabelText('progress-circular-loader')).toBeVisible();
            expect(screen.getByText('50%')).toBeVisible();
        }
    );

    it.each([
        { status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR },
        { status: DATASET_IMPORT_STATUSES.PREPARING_ERROR },
        { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR },
        { status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR },
    ])(
        'should render "CircularLoader" and "N/A" inside it when datasetImportItem status is "$status"',
        async ({ status }) => {
            await renderApp({ ...mockDatasetImportItem, status });
            expect(screen.getByLabelText('progress-circular-loader')).toBeVisible();
            expect(screen.getByText('N/A')).toBeVisible();
        }
    );
});
