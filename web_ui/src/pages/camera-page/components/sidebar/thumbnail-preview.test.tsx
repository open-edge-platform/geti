// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { getMockedScreenshot } from '../../../../test-utils/mocked-items-factory/mocked-camera';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { configUseCameraStorage } from '../../test-utils/config-use-camera';
import { ThumbnailPreview } from './thumbnail-preview.component';

jest.mock('../../hooks/use-camera-storage.hook', () => ({
    ...jest.requireActual('../../hooks/use-camera-storage.hook'),
    useCameraStorage: jest.fn(),
}));

describe('ThumbnailPreview', () => {
    const mockedScreenshot = getMockedScreenshot({});

    beforeAll(() => {
        jest.useFakeTimers();
    });

    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    const renderApp = async ({
        mockedDeleteMany = jest.fn(() => Promise.resolve()),
        mockedSaveMedia = jest.fn(),
    }: {
        mockedDeleteMany?: jest.Mock;
        mockedSaveMedia?: jest.Mock;
    }) => {
        configUseCameraStorage({ saveMedia: mockedSaveMedia, deleteMany: mockedDeleteMany });

        render(
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
                <ThumbnailPreview screenshots={[mockedScreenshot]} />
            </ProjectProvider>
        );

        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
    };

    it('toggle image animation classes', async () => {
        await renderApp({});

        fireEvent.click(screen.getByRole('button', { name: 'open preview' }));
        jest.advanceTimersByTime(1000);

        expect(screen.getByRole('img', { name: `full screen screenshot ${mockedScreenshot.id}` })).toHaveClass(
            'thumbnailPreviewImageOpened'
        );

        fireEvent.click(screen.getByRole('button', { name: 'close preview' }));
        jest.advanceTimersByTime(1000);

        expect(
            screen.queryByRole('img', { name: `full screen screenshot ${mockedScreenshot.id}` })
        ).not.toBeInTheDocument();
    });

    it('call onDelete', async () => {
        const mockedDeleteMany = jest.fn(() => Promise.resolve());

        await renderApp({ mockedDeleteMany });

        fireEvent.click(screen.getByRole('button', { name: 'open preview' }));
        jest.advanceTimersByTime(1000);
        fireEvent.click(screen.getByRole('button', { name: /delete/i }));

        fireEvent.click(await screen.findByRole('button', { name: /delete/i }));

        expect(mockedDeleteMany).toHaveBeenCalledWith([mockedScreenshot.id]);

        await waitFor(() => {
            expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
        });
    });
});
