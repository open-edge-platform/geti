// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { QueryClient } from '@tanstack/react-query';
import { waitFor } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { createInMemoryMediaService } from '../../../../core/media/services/in-memory-media-service/in-memory-media-service';
import { MediaService } from '../../../../core/media/services/media-service.interface';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { renderHookWithProviders } from '../../../../test-utils/render-hook-with-providers';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { filterPageMedias } from '../../utils';
import { useDeleteMediaMutation } from './media-delete.hook';

const mockSetQueriesData = jest.fn();
const mockAddNotification = jest.fn();

jest.mock('../../utils', () => ({
    ...jest.requireActual('../../utils'),
    filterPageMedias: jest.fn(),
}));

jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

const mockedImageMedia = getMockedImageMediaItem({
    name: 'image-1',
    identifier: { type: MEDIA_TYPE.IMAGE, imageId: '1111' },
});
const mockedImageMediaTwo = getMockedImageMediaItem({
    name: 'image-2',
    identifier: { type: MEDIA_TYPE.IMAGE, imageId: '2222' },
});

const renderDeleteMediaMutationHook = ({
    mediaService = createInMemoryMediaService(),
}: {
    mediaService?: MediaService;
} = {}) => {
    const queryClient = new QueryClient();
    queryClient.setQueriesData = mockSetQueriesData;

    return renderHookWithProviders(useDeleteMediaMutation, {
        wrapper: ({ children }) => (
            <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>{children}</ProjectProvider>
        ),
        providerProps: { mediaService, queryClient },
    });
};

const mockedResponse = {
    pages: [
        {
            media: [mockedImageMedia, mockedImageMediaTwo],
            totalImages: 1,
            totalMatchedImages: 1,
            totalVideos: 0,
            totalMatchedVideoFrames: 0,
            totalMatchedVideos: 0,
        },
    ],
    pageParams: [null],
};

describe('useDeleteMediaMutation', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockSetQueriesData.mockImplementationOnce((_queries, updater) => updater(mockedResponse));
    });

    it('optimistic update calls "filterPageMedias"', async () => {
        const { result } = renderDeleteMediaMutationHook();

        await waitFor(() => {
            expect(result.current).toBeTruthy();
        });

        result.current.deleteMedia.mutate([mockedImageMedia]);

        await waitFor(() => {
            expect(filterPageMedias).toHaveBeenCalled();
            expect(mockSetQueriesData).toHaveBeenCalledTimes(1);
            expect(mockAddNotification).not.toHaveBeenCalled();
        });
    });

    it('if an error is caught restores the previous states', async () => {
        const errorMessage = 'test-error';

        const mediaService = createInMemoryMediaService();
        mediaService.deleteMedia = () => Promise.reject({ response: { data: { message: errorMessage } } });

        const { result } = renderDeleteMediaMutationHook({ mediaService });

        await waitFor(() => {
            expect(result.current).toBeTruthy();
        });

        result.current.deleteMedia.mutate([mockedImageMedia]);

        await waitFor(() => {
            expect(filterPageMedias).toHaveBeenCalled();
            expect(mockSetQueriesData).toHaveBeenCalledTimes(2);
            expect(mockAddNotification).toHaveBeenCalledWith({
                message: `Media cannot be deleted. ${errorMessage}`,
                type: NOTIFICATION_TYPE.ERROR,
            });
        });
    });
});
