// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useUsers } from '@geti/core/src/users/hook/use-users.hook';
import { screen, waitFor } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { getMockedUser } from '../../../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { MediaItemTooltipMessage, MediaItemTooltipMessageProps } from './media-item-tooltip-message';

const mockedUser = getMockedUser({ id: 'user@intel.com' });
jest.mock('@geti/core/src/users/hook/use-users.hook', () => ({
    useUsers: jest.fn(() => ({
        useGetUserQuery: jest.fn(() => ({
            data: mockedUser,
            retry: 0,
        })),
    })),
}));

describe('MediaItemTooltipMessage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('returns correct information for images', async () => {
        const props: MediaItemTooltipMessageProps = {
            fileName: 'Sir file',
            resolution: '4k',
            id: '1234',
            type: MEDIA_TYPE.IMAGE,
            uploadTime: '2022-06-29T14:19:02.738Z',
            uploaderId: '6b3b8453-92a2-41ef-9725-63badb218504',
            fileSize: '3 MB',
            lastAnnotatorId: '6b3b8453-92a2-41ef-9725-63badb218504',
        };

        const { fileName, resolution, fileSize } = props;

        render(<MediaItemTooltipMessage {...props} />);

        expect(screen.getByText(`File name: ${fileName}`)).toBeInTheDocument();
        expect(screen.getByText(`Size: ${fileSize}`)).toBeInTheDocument();
        expect(screen.getByText(`Resolution: ${resolution}`)).toBeInTheDocument();
        expect(screen.getByText('Upload time: 29 Jun 2022 14:19:02')).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText('Owner: Test User')).toBeInTheDocument();
            expect(screen.getByText('Last annotator: Test User')).toBeInTheDocument();
        });
    });

    it('returns correct information for videos', async () => {
        const props: MediaItemTooltipMessageProps = {
            fileName: 'Sir file',
            resolution: '4k',
            fps: 30,
            id: '1234',
            type: MEDIA_TYPE.VIDEO,
            duration: 30,
            uploadTime: '2022-06-29T14:19:02.738Z',
            uploaderId: '6b3b8453-92a2-41ef-9725-63badb218504',
            fileSize: '3 MB',
            lastAnnotatorId: '6b3b8453-92a2-41ef-9725-63badb218504',
        };

        render(<MediaItemTooltipMessage {...props} />);

        expect(screen.getByText(`File name: Sir file`)).toBeInTheDocument();
        expect(screen.getByText(`Size: 3 MB`)).toBeInTheDocument();
        expect(screen.getByText(`Resolution: ${props.resolution}`)).toBeInTheDocument();
        expect(screen.getByText(`FPS: 30.00`)).toBeInTheDocument();
        expect(screen.getByText(`Duration: 30s`)).toBeInTheDocument();
        expect(screen.getByText('Upload time: 29 Jun 2022 14:19:02')).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText('Owner: Test User')).toBeInTheDocument();
            expect(screen.getByText('Last annotator: Test User')).toBeInTheDocument();
        });
    });

    it('returns correct information with invalid user id', async () => {
        jest.mocked(useUsers).mockImplementationOnce(() => ({
            // @ts-expect-error We only care about one query returning 'undefined'
            useGetUserQuery: jest.fn(() => ({
                data: undefined,
            })),
        }));
        const props: MediaItemTooltipMessageProps = {
            fileName: 'Sir file',
            resolution: '4k',
            id: '1234',
            type: MEDIA_TYPE.IMAGE,
            uploadTime: '2022-06-29T14:19:02.738Z',
            uploaderId: 'user@intel.com',
            fileSize: '3 MB',
            lastAnnotatorId: 'user@intel.com',
        };

        const { fileName, resolution, fileSize } = props;

        render(<MediaItemTooltipMessage {...props} />);

        expect(screen.getByText(`File name: ${fileName}`)).toBeInTheDocument();
        expect(screen.getByText(`Size: ${fileSize}`)).toBeInTheDocument();
        expect(screen.getByText(`Resolution: ${resolution}`)).toBeInTheDocument();
        expect(screen.getByText('Upload time: 29 Jun 2022 14:19:02')).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText('Owner: Unknown user')).toBeInTheDocument();
            expect(screen.getByText('Last annotator: Unknown user')).toBeInTheDocument();
        });
    });

    it('hides video sections if media type is "Video frame"', async () => {
        const props: MediaItemTooltipMessageProps = {
            fileName: 'Sir file',
            resolution: '4k',
            id: '1234',
            type: MEDIA_TYPE.VIDEO_FRAME,
            uploadTime: '2022-06-29T14:19:02.738Z',
            uploaderId: 'user@intel.com',
            fileSize: '',
            lastAnnotatorId: 'user@intel.com',
        };

        const { fileName, resolution } = props;

        render(<MediaItemTooltipMessage {...props} />);

        expect(screen.getByText(`File name: ${fileName}`)).toBeInTheDocument();
        expect(screen.getByText(`Resolution: ${resolution}`)).toBeInTheDocument();
        expect(screen.getByText('Upload time: 29 Jun 2022 14:19:02')).toBeInTheDocument();
        expect(screen.queryByText(/size/)).not.toBeInTheDocument();
        expect(screen.queryByText(/fps/)).not.toBeInTheDocument();
        expect(screen.queryByText(/duration/)).not.toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText('Owner: Test User')).toBeInTheDocument();
            expect(screen.getByText('Last annotator: Test User')).toBeInTheDocument();
        });
    });
});
