// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { mockGlobalFile } from '../../../../test-utils/mockFile';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { UserPhotoContainer } from './user-photo-container.component';
import { USER_PHOTO_VALIDATION_MESSAGES } from './utils';

const mockAddNotification = jest.fn();

jest.mock('../../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

describe('UserPhotoContainer', () => {
    const renderUserPhoto = (userPhoto: string | null = null, userName = 'test-user') => {
        render(
            <UserPhotoContainer
                userId={'test-user'}
                userName={userName}
                email={'test@mail.com'}
                userPhoto={userPhoto}
            />
        );
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const uploadFile = async (fileSize: number) => {
        const file = mockGlobalFile('user.png', fileSize);

        // TODO: investigate why userEvent.upload does not work with current accept property of the input
        const user = userEvent.setup({ applyAccept: false });

        await user.upload(screen.getByLabelText('Upload user photo'), file);

        return file;
    };

    it('should show an error when user photo is too big', async () => {
        const fileSize = 1024 * 1024; // 1 MiB

        renderUserPhoto();

        await uploadFile(fileSize);

        await waitFor(() => {
            expect(mockAddNotification).toHaveBeenCalledWith({
                message: USER_PHOTO_VALIDATION_MESSAGES.MAX_SIZE,
                type: NOTIFICATION_TYPE.ERROR,
            });
        });
    });

    // eslint-disable-next-line jest/no-disabled-tests
    it.skip("should show mocked user's photo when there is no photo", async () => {
        const userName = 'TestName';
        renderUserPhoto(null, userName);

        expect(screen.getByText(userName.charAt(0))).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /upload image/i })).toBeInTheDocument();

        expect(screen.queryByRole('button', { name: /change/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /remove/i })).not.toBeInTheDocument();
    });

    it("should not show mocked user's photo when photo is uploaded", async () => {
        const userName = 'TestName';
        renderUserPhoto('linkToPhoto', userName);

        expect(screen.queryByText(userName.charAt(0))).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /upload image/i })).not.toBeInTheDocument();

        expect(screen.getByRole('button', { name: /change/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /remove/i })).toBeInTheDocument();
    });

    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('should show picture limits', async () => {
        const userName = 'TestName';
        renderUserPhoto('linkToPhoto', userName);

        jest.useFakeTimers();

        await userEvent.hover(screen.getByText('Picture limits'));

        jest.advanceTimersByTime(1000);

        expect(screen.getByRole('tooltip')).toBeInTheDocument();
        expect(screen.getByTestId('picture-limits-id')).toBeInTheDocument();

        jest.useRealTimers();
    });

    it('should not show picture limits for account service', async () => {
        renderUserPhoto('linkToPhoto', 'TestName');

        expect(screen.queryByText('Picture limits')).not.toBeInTheDocument();
    });
});
