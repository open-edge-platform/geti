// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import '@wessberg/pointer-events';

import { ReactElement } from 'react';

import { screen } from '@testing-library/react';

import { createInMemoryUsersService } from '../../../../core/users/services/in-memory-users-service';
import { getMockedVideoMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { getMockedUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { projectRender } from '../../../../test-utils/project-provider-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { MediaProvider } from '../../../media/providers/media-provider.component';
import { MediaItemDetails } from './media-item-details.component';

const render = async (ui: ReactElement, options?: Parameters<typeof projectRender>[1]) => {
    await projectRender(<MediaProvider>{ui}</MediaProvider>, options);
};

describe('MediaItemDetails', () => {
    it('Check if there is frames indicator if video is filtered', async () => {
        const mockedMediaVideo = getMockedVideoMediaItem({ name: 'video 1', matchedFrames: 7 });

        await render(
            <MediaProvider>
                <MediaItemDetails
                    id={'test-media-item'}
                    isSelected={false}
                    mediaItem={mockedMediaVideo}
                    shouldShowAnnotationIndicator={true}
                    handleDblClick={jest.fn()}
                    toggleMediaSelection={jest.fn()}
                />
            </MediaProvider>
        );

        expect(screen.getByRole('checkbox', { name: 'Select media item' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'open menu' })).toBeInTheDocument();

        expect(screen.getByTestId('video-indicator-duration-id')).toBeInTheDocument();
        expect(screen.getByTestId('video-indicator-frames-id')).toBeInTheDocument();
    });

    it('Check if there is no frames indicator if video is not filtered', async () => {
        const mockedMediaVideo = getMockedVideoMediaItem({ name: 'video 1' });

        await render(
            <MediaItemDetails
                id={'test-media-item'}
                isSelected={false}
                mediaItem={mockedMediaVideo}
                shouldShowAnnotationIndicator={true}
                handleDblClick={jest.fn()}
                toggleMediaSelection={jest.fn()}
            />
        );

        expect(screen.getByTestId('video-indicator-duration-id')).toBeInTheDocument();
        expect(screen.queryByTestId('video-indicator-frames-id')).not.toBeInTheDocument();
    });

    it('Check if there are proper tooltips on video frames and duration', async () => {
        const mockedMediaVideo = getMockedVideoMediaItem({ name: 'video 1', matchedFrames: 7 });

        await render(
            <MediaItemDetails
                id={'test-media-item'}
                isSelected={false}
                mediaItem={mockedMediaVideo}
                shouldShowAnnotationIndicator={true}
                handleDblClick={jest.fn()}
                toggleMediaSelection={jest.fn()}
            />
        );

        const framesIndicator = screen.getByText(`${mockedMediaVideo.matchedFrames} frames`);
        await checkTooltip(framesIndicator, 'Filtered number of frames');

        const durationIndicator = screen.getByText('00:10:00');
        await checkTooltip(durationIndicator, 'Duration of the video');
    });

    it('Check media items common data', async () => {
        const mockedMediaVideo = getMockedVideoMediaItem({
            name: 'video 1',
            matchedFrames: 7,
            uploaderId: '6b3b8453-92a2-41ef-9725-63badb218504',
        });
        const mockedUsersService = createInMemoryUsersService();
        mockedUsersService.getUser = async () => {
            return getMockedUser({ id: 'uploader-id', firstName: 'John', lastName: 'Stamina' });
        };

        await render(
            <MediaItemDetails
                id={'test-media-item'}
                isSelected={false}
                mediaItem={mockedMediaVideo}
                shouldShowAnnotationIndicator={true}
                handleDblClick={jest.fn()}
                toggleMediaSelection={jest.fn()}
            />,
            { services: { usersService: mockedUsersService } }
        );

        const itemNameElement = screen.getByText(mockedMediaVideo.name);
        await checkTooltip(itemNameElement, `Name: ${mockedMediaVideo.name}`);

        const uploadTimeElement = screen.getByText('22.06.2022');
        await checkTooltip(uploadTimeElement, 'Upload date: 22.06.2022');

        const fileSizeElement = screen.getByText('123.46 KB');
        await checkTooltip(fileSizeElement, 'File size: 123.46 KB');

        const uploaderElement = screen.getByText('John Stamina');
        await checkTooltip(uploaderElement, `Uploader: John Stamina`);
    });

    it('Returns correct uploader info with invalid user id', async () => {
        const mockedMediaVideo = getMockedVideoMediaItem({
            name: 'video 1',
            matchedFrames: 7,
            uploaderId: 'user@intel.com',
        });
        const mockedUsersService = createInMemoryUsersService();
        mockedUsersService.getUser = async () => {
            return getMockedUser({ id: 'user@intel.com' });
        };

        await render(
            <MediaProvider>
                <MediaItemDetails
                    id={'test-media-item'}
                    isSelected={false}
                    mediaItem={mockedMediaVideo}
                    shouldShowAnnotationIndicator={true}
                    handleDblClick={jest.fn()}
                    toggleMediaSelection={jest.fn()}
                />
            </MediaProvider>,
            { services: { usersService: mockedUsersService } }
        );

        const itemNameElement = screen.getByText(mockedMediaVideo.name);
        await checkTooltip(itemNameElement, `Name: ${mockedMediaVideo.name}`);

        const uploadTimeElement = screen.getByText('22.06.2022');
        await checkTooltip(uploadTimeElement, 'Upload date: 22.06.2022');

        const fileSizeElement = screen.getByText('123.46 KB');
        await checkTooltip(fileSizeElement, 'File size: 123.46 KB');

        const uploaderElement = screen.getByText('Unknown user');
        await checkTooltip(uploaderElement, `Uploader: Unknown user`);
    });
});
