// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { waitFor } from '@testing-library/react';

import { DATASET_IMPORT_STATUSES } from '../../core/datasets/dataset.enum';
import { createInMemoryDatasetImportService } from '../../core/datasets/services/in-memory-dataset-import-service';
import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';
import { getMockedWorkspaceIdentifier } from '../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedDatasetImportItem } from '../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { DatasetImportToNewProjectProvider } from './dataset-import-to-new-project-provider.component';

const mockedWorkspaceIdentifier = getMockedWorkspaceIdentifier();

jest.mock('../workspaces-provider/use-workspace-identifier.hook', () => ({
    ...jest.requireActual('../workspaces-provider/use-workspace-identifier.hook'),
    useWorkspaceIdentifier: jest.fn(() => mockedWorkspaceIdentifier),
}));

const mockedDatasetImportService = createInMemoryDatasetImportService();
mockedDatasetImportService.prepareDatasetJob = jest.fn().mockResolvedValue({ jobId: '123' });

describe('DatasetImportToNewProjectProvider', () => {
    const renderApp = async () => {
        render(<DatasetImportToNewProjectProvider>Import App</DatasetImportToNewProjectProvider>, {
            services: { datasetImportService: mockedDatasetImportService },
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('prepare import', () => {
        const mockedDatasetImportItem = getMockedDatasetImportItem({ status: DATASET_IMPORT_STATUSES.PREPARING });

        it('call new prepare dataset job if preparingJobId is empty', async () => {
            global.localStorage.setItem(
                `${LOCAL_STORAGE_KEYS.IMPORT_DATASET_TO_NEW_PROJECT}-${mockedWorkspaceIdentifier.organizationId}-${mockedWorkspaceIdentifier.workspaceId}`,
                JSON.stringify([{ ...mockedDatasetImportItem, preparingJobId: undefined }])
            );

            await renderApp();

            await waitFor(() => {
                expect(mockedDatasetImportService.prepareDatasetJob).toHaveBeenCalledWith(
                    expect.objectContaining({ uploadId: mockedDatasetImportItem.uploadId })
                );
            });
        });

        it('do not call new prepare dataset it has a valid preparingJobId', async () => {
            global.localStorage.setItem(
                `${LOCAL_STORAGE_KEYS.IMPORT_DATASET_TO_NEW_PROJECT}-${mockedWorkspaceIdentifier.organizationId}-${mockedWorkspaceIdentifier.workspaceId}`,
                JSON.stringify([{ ...mockedDatasetImportItem, preparingJobId: '321' }])
            );

            await renderApp();

            expect(mockedDatasetImportService.prepareDatasetJob).not.toHaveBeenCalled();
        });
    });
});
