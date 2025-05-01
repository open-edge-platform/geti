// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider } from '@adobe/react-spectrum';
import { downloadFile, getDownloadNotificationMessage } from '@shared/utils';
import { fireEvent, RenderResult, screen } from '@testing-library/react';

import { ExportDatasetLSData, ExportFormats } from '../../../../../core/projects/dataset.interface';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ExportDatasetDownload } from './export-dataset-download.component';

jest.mock('../../../hooks/use-export-dataset.hook', () => ({
    ...jest.requireActual('../../../hooks/use-export-dataset.hook'),
    useExportDataset: jest.fn(() => ({ exportDatasetStatus: {} })),
}));
jest.mock('@shared/utils', () => ({
    ...jest.requireActual('@shared/utils'),
    downloadFile: jest.fn(),
}));

const mockLocalStorage: ExportDatasetLSData = {
    datasetId: '123',
    exportFormat: ExportFormats.COCO,
    isPrepareDone: false,
    exportDatasetId: '321',
    downloadUrl: 'downloadUrl-test',
    datasetName: 'testDataset',
};

describe('ExportDatasetDownload', () => {
    const renderApp = (
        localStorageData = mockLocalStorage
    ): { mockOnCloseDownload: jest.Mock; component: RenderResult } => {
        const mockOnCloseDownload = jest.fn();

        const component = render(
            <Provider theme={defaultTheme}>
                <ExportDatasetDownload localStorageData={localStorageData} onCloseDownload={mockOnCloseDownload} />
            </Provider>
        );

        return { mockOnCloseDownload, component };
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('empty `localStorageData` return empty', async () => {
        renderApp({ ...mockLocalStorage, downloadUrl: '' });

        expect(screen.queryByLabelText('export-dataset-download')).not.toBeInTheDocument();
    });

    it('calls "onCloseDownload" after closing', async () => {
        const { mockOnCloseDownload } = renderApp();

        fireEvent.click(screen.getByRole('button', { name: 'Close' }));

        expect(mockOnCloseDownload).toHaveBeenNthCalledWith(1, mockLocalStorage.datasetId);
    });

    it('triggers download and closes the view', async () => {
        const { mockOnCloseDownload } = renderApp();

        fireEvent.click(screen.getByRole('button', { name: 'Download' }));

        expect(downloadFile).toHaveBeenCalledWith(
            `/api/${mockLocalStorage.downloadUrl}`,
            `intel_geti_${mockLocalStorage.datasetId}.zip`
        );
        expect(mockOnCloseDownload).toHaveBeenCalledWith(mockLocalStorage.datasetId);
        expect(await screen.findByText(getDownloadNotificationMessage('dataset'))).toBeInTheDocument();
    });

    it('renders dataset size after job "prepare" step is done', async () => {
        renderApp({ ...mockLocalStorage, downloadUrl: 'fake-download-url', isPrepareDone: true, size: 12000000 });

        expect(screen.getByText('Dataset "testDataset" is ready to download.')).toBeInTheDocument();
        expect(screen.getByText('Format: COCO')).toBeInTheDocument();
        expect(screen.getByText('Size: 12 MB')).toBeInTheDocument();
    });
});
