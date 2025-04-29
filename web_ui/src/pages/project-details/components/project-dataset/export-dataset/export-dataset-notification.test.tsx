// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useOverlayTriggerState } from '@react-stately/overlays';
import { RenderResult, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { JobState } from '../../../../../core/jobs/jobs.const';
import { DatasetIdentifier, ExportFormats } from '../../../../../core/projects/dataset.interface';
import { createInMemoryProjectService } from '../../../../../core/projects/services/in-memory-project-service';
import { getMockedDatasetIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedDatasetExportJob } from '../../../../../test-utils/mocked-items-factory/mocked-jobs';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ExportDatasetNotification } from './export-dataset-notification.component';

const mockDatasetIdentifier: DatasetIdentifier = getMockedDatasetIdentifier({
    datasetId: '123',
    projectId: '412',
    workspaceId: '321',
});

const mockExportDatasetLSData = {
    isPrepareDone: false,
    exportDatasetId: '231',
    exportFormat: ExportFormats.VOC,
    datasetId: mockDatasetIdentifier.datasetId,
    downloadUrl: 'downloadUrl-test',
};

const mockUpdateLsExportDataset = jest.fn();
const mockRemoveDatasetLsByDatasetId = jest.fn();
const mockGetDatasetLsByDatasetId = jest.fn();
jest.mock('../../../hooks/use-local-storage-export-dataset.hook', () => ({
    useLocalStorageExportDataset: () => ({
        getDatasetLsByDatasetId: mockGetDatasetLsByDatasetId,
        updateLsExportDataset: mockUpdateLsExportDataset,
        removeDatasetLsByDatasetId: mockRemoveDatasetLsByDatasetId,
    }),
}));

const App = () => {
    const visibilityState = useOverlayTriggerState({});

    return (
        <>
            <button onClick={() => visibilityState.open()}>open dialog</button>
            <ExportDatasetNotification visibilityState={visibilityState} datasetIdentifier={mockDatasetIdentifier} />
        </>
    );
};

const renderApp = async (isOpen = true, projectService = createInMemoryProjectService()): Promise<RenderResult> => {
    const component = render(<App />, {
        services: { projectService },
    });

    isOpen && (await userEvent.click(screen.getByText('open dialog')));

    return component;
};

describe('ExportDatasetNotification', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders empty when local storage does not have export dataset info', async () => {
        await renderApp();

        expect(screen.queryByLabelText('export-dataset-notifications')).not.toBeInTheDocument();
        expect(mockGetDatasetLsByDatasetId).toHaveBeenLastCalledWith(mockDatasetIdentifier.datasetId);
    });

    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('closes exportStatus and opens exportDownload', async () => {
        const projectService = createInMemoryProjectService();
        projectService.exportDatasetStatusJob = async () =>
            Promise.resolve(getMockedDatasetExportJob({ state: JobState.RUNNING }));

        mockGetDatasetLsByDatasetId.mockReturnValue(mockExportDatasetLSData);

        await renderApp(true, projectService);
        expect(screen.queryByLabelText('export-dataset-status')).toBeInTheDocument();

        projectService.exportDatasetStatusJob = async () =>
            Promise.resolve(getMockedDatasetExportJob({ state: JobState.FINISHED }));

        mockGetDatasetLsByDatasetId.mockReturnValue(undefined);

        await waitFor(() => {
            expect(screen.queryByLabelText('export-dataset-status')).not.toBeInTheDocument();
            expect(screen.queryByLabelText('export-dataset-download')).toBeInTheDocument();
        });
    });

    it('closes exportDownload and exportNotification', async () => {
        mockGetDatasetLsByDatasetId.mockReturnValue({ ...mockExportDatasetLSData, isPrepareDone: true });
        await renderApp();
        expect(screen.queryByLabelText('export-dataset-download')).toBeInTheDocument();

        mockGetDatasetLsByDatasetId.mockReturnValue(undefined);
        await userEvent.click(screen.getByRole('button', { name: 'Close' }));
        expect(mockRemoveDatasetLsByDatasetId).toHaveBeenNthCalledWith(1, mockExportDatasetLSData.datasetId);
        expect(screen.queryByLabelText('export-dataset-download')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('export-dataset-notifications')).not.toBeInTheDocument();
    });

    it('reopens with ExportDatasetStatus', async () => {
        mockGetDatasetLsByDatasetId.mockReturnValue(mockExportDatasetLSData);
        await renderApp(false);

        expect(screen.queryByLabelText('export-dataset-status')).toBeInTheDocument();
        expect(screen.queryByLabelText('export-dataset-download')).not.toBeInTheDocument();
    });

    it('reopens with dataset-download', async () => {
        mockGetDatasetLsByDatasetId.mockReturnValue({ ...mockExportDatasetLSData, isPrepareDone: true });
        await renderApp(false);

        expect(screen.queryByLabelText('export-dataset-download')).toBeInTheDocument();
        expect(screen.queryByLabelText('export-dataset-status')).not.toBeInTheDocument();
    });
});
