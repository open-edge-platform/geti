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

import { fireEvent, screen, waitFor } from '@testing-library/react';

import { MenuItemsKey } from '../../../../../shared/components/upload-media/upload-media-button/upload-media-button.interface';
import { onMenuAction } from '../../../../../shared/components/upload-media/utils';
import {
    getMockedDatasetIdentifier,
    getMockedProjectIdentifier,
} from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { ProjectProvider } from '../../../providers/project-provider/project-provider.component';
import { UploadImageButton } from './upload-image-button.component';

jest.mock('../../../../annotator/hooks/use-dataset-identifier.hook');

const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockedNavigate,
}));

jest.mock('../../../../../shared/components/upload-media/utils', () => ({
    ...jest.requireActual('../../../../../shared/components/upload-media/utils'),
    onMenuAction: jest.fn(),
}));

const mockedDatasetIdentifier = getMockedDatasetIdentifier();

describe('UploadImageButton', () => {
    const renderApp = async ({
        isDisabled = false,
        mockedHandleUploadImage = jest.fn(),
    }: {
        isDisabled?: boolean;
        mockedHandleUploadImage?: jest.Mock;
    }) => {
        await render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
                <UploadImageButton handleUploadImage={mockedHandleUploadImage} isDisabled={isDisabled} />
            </ProjectProvider>
        );
    };

    beforeEach(() => {
        jest.mocked(useDatasetIdentifier).mockReturnValue(mockedDatasetIdentifier);
    });

    it('upload button calls "onMenuAction"', async () => {
        await renderApp({});

        const uploadButton = screen.getByRole('button', { name: /upload/i });

        await waitFor(() => {
            expect(uploadButton).toBeEnabled();
        });

        fireEvent.click(uploadButton);
        fireEvent.click(screen.getByRole('menuitem', { name: /file/i }));

        expect(onMenuAction).toHaveBeenCalledWith(MenuItemsKey.FILE.toLowerCase(), expect.any(Object));
    });

    it('is disabled when passing disable', async () => {
        await renderApp({ mockedHandleUploadImage: jest.fn(), isDisabled: true });

        expect(screen.getByRole('button')).toBeDisabled();
    });

    describe('Camera options', () => {
        it('render menu options', async () => {
            await renderApp({});

            const uploadButton = screen.getByRole('button', { name: /upload/i });

            await waitFor(() => {
                expect(uploadButton).toBeEnabled();
            });

            fireEvent.click(uploadButton);

            expect(screen.getByRole('menuitem', { name: /file/i })).toBeVisible();
            expect(screen.getByRole('menuitem', { name: /camera/i })).toBeVisible();
        });

        it('file option calls "onMenuAction"', async () => {
            await renderApp({});

            const uploadButton = screen.getByRole('button', { name: /upload/i });

            await waitFor(() => {
                expect(uploadButton).toBeEnabled();
            });

            fireEvent.click(uploadButton);

            fireEvent.click(screen.getByRole('menuitem', { name: /file/i }));

            expect(onMenuAction).toHaveBeenCalledWith(MenuItemsKey.FILE.toLowerCase(), expect.any(Object));
        });

        it('camera option redirects to camera page on livePrediction mode', async () => {
            await renderApp({});

            const uploadButton = screen.getByRole('button', { name: /upload/i });

            await waitFor(() => {
                expect(uploadButton).toBeEnabled();
            });

            fireEvent.click(uploadButton);
            fireEvent.click(screen.getByRole('menuitem', { name: /camera/i }));

            expect(mockedNavigate).toHaveBeenCalledWith(expect.stringContaining('/camera?isLivePrediction=true'));
        });
    });
});
