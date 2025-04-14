// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider } from '@adobe/react-spectrum';
import { UseQueryResult } from '@tanstack/react-query';
import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { AxiosError } from 'axios';

import { paths } from '../../../../core/services/routes';
import { useStatus } from '../../../../core/status/hooks/use-status.hook';
import { TOO_LOW_FREE_DISK_SPACE_IN_BYTES } from '../../../../core/status/hooks/utils';
import { StatusProps } from '../../../../core/status/status.interface';
import { ProjectProvider } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { DIRECTORY_ATTRS } from '../utils';
import { UploadMediaButton } from './upload-media-button.component';
import { MenuItemsKey } from './upload-media-button.interface';

const datasetIdentifier = {
    workspaceId: 'workspace-id',
    projectId: 'project-id',
    datasetId: 'dataset-id',
};

jest.mock('../../../../pages/annotator/hooks/use-dataset-identifier.hook', () => ({
    useDatasetIdentifier: () => datasetIdentifier,
}));

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
}));

const mockedAddNotification = jest.fn();
jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockedAddNotification }),
}));

jest.mock('../../../../core/status/hooks/use-status.hook', () => ({
    ...jest.requireActual('../../../../core/status/hooks/use-status.hook'),
    useStatus: jest.fn(),
}));

describe('UploadMediaButton', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const getInputFile = () => screen.getByLabelText('upload-media-input');
    const selectOption = (option = MenuItemsKey.FOLDER) => {
        fireEvent.click(screen.getByLabelText('Upload media'));
        fireEvent.click(screen.getByLabelText(option));
    };
    const fireInputChange = (mockFile: (File | null)[]) => {
        const positions = mockFile.reduce<{ [key: string]: File | null }>((accum, current, index) => {
            accum[String(index)] = current;
            return accum;
        }, {});

        fireEvent.change(getInputFile(), {
            target: {
                files: {
                    item: (index: number) => mockFile[index],
                    length: mockFile.length,
                    ...positions,
                },
            },
        });
    };

    const renderApp = async ({
        onCameraSelected = jest.fn(),
        uploadCallback = jest.fn(),
        freeSpace = TOO_LOW_FREE_DISK_SPACE_IN_BYTES + 1,
        multiple = true,
        initialEntries = [''],
    }: {
        uploadCallback?: jest.Mock;
        multiple?: boolean;
        freeSpace?: number;
        cameraFlag?: boolean;
        initialEntries?: string[];
        onCameraSelected?: jest.Mock;
    }) => {
        jest.mocked(useStatus).mockReturnValue({
            data: { freeSpace, totalSpace: 10, runningJobs: 0 },
        } as UseQueryResult<StatusProps, AxiosError>);

        render(
            <ProjectProvider
                projectIdentifier={{
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                    organizationId: 'org-id',
                }}
            >
                <Provider theme={defaultTheme}>
                    <UploadMediaButton
                        id='test'
                        title='options'
                        multiple={multiple}
                        uploadCallback={uploadCallback}
                        onCameraSelected={onCameraSelected}
                    />
                </Provider>
            </ProjectProvider>,
            {
                initialEntries,
            }
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('updates input properties upon selecting "File"', async () => {
        const mockUploadCallback = jest.fn();

        await renderApp({ uploadCallback: mockUploadCallback });
        DIRECTORY_ATTRS.forEach((attr) => expect(getInputFile()).not.toHaveAttribute(attr));

        selectOption();

        DIRECTORY_ATTRS.forEach((attr) => expect(getInputFile()).toHaveAttribute(attr));
    });

    it('calls "uploadCallback"', async () => {
        const mockUploadCallback = jest.fn();
        const mockFile = new File(['test'], 'test.png', { type: 'image/png' });

        await renderApp({ uploadCallback: mockUploadCallback });
        selectOption();
        fireInputChange([mockFile, null, mockFile]);

        expect(mockUploadCallback).toHaveBeenCalledWith([mockFile, mockFile]);
        expect(mockedAddNotification).not.toHaveBeenCalled();
    });

    it('shows empty folder warning', async () => {
        const mockUploadCallback = jest.fn();
        const mockFile = new File(['test'], 'test.png', { type: 'image/png' });

        await renderApp({ uploadCallback: mockUploadCallback });

        selectOption();
        fireInputChange([]);

        expect(mockedAddNotification).toHaveBeenCalled();
        expect(mockUploadCallback).not.toHaveBeenCalledWith([mockFile]);
    });

    describe('low storage space disables import options', () => {
        it('multiple files', async () => {
            const mockUploadCallback = jest.fn();

            await renderApp({ uploadCallback: mockUploadCallback, freeSpace: 0 });

            expect(getInputFile()).toBeDisabled();
            expect(screen.getByLabelText('Upload media')).toBeDisabled();
        });

        it('single file', async () => {
            const mockUploadCallback = jest.fn();

            await renderApp({ uploadCallback: mockUploadCallback, freeSpace: 0, multiple: false });

            expect(getInputFile()).toBeDisabled();
            expect(screen.getByLabelText('Upload media')).toBeDisabled();
        });
    });

    describe('Camera upload', () => {
        it('single file and camera', async () => {
            const mockUploadCallback = jest.fn();

            await renderApp({ uploadCallback: mockUploadCallback, multiple: false });
            fireEvent.click(screen.getByLabelText('Upload media'));

            expect(screen.getByLabelText(MenuItemsKey.FILE)).toBeVisible();
            expect(screen.getByLabelText(MenuItemsKey.CAMERA)).toBeVisible();
        });

        it('calls onCameraSelected', async () => {
            const mockedOnCameraSelected = jest.fn();
            await renderApp({
                multiple: false,
                onCameraSelected: mockedOnCameraSelected,
                initialEntries: [paths.project.tests.livePrediction.pattern],
            });

            selectOption(MenuItemsKey.CAMERA);

            expect(mockedOnCameraSelected).toHaveBeenCalled();
        });
    });
});
