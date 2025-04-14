// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useClipboard } from './use-clipboard.hook';

const mockwriteText = jest.fn();
Object.assign(navigator, {
    clipboard: {
        writeText: mockwriteText,
    },
});

const mockAddNotification = jest.fn();
jest.mock('../../notification/notification.component', () => ({
    ...jest.requireActual('../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

describe('useClipboard', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('Copy and shows a info notification message', async () => {
        mockwriteText.mockResolvedValue(true);
        const textToCopy = 'this is a test';
        const confirmationMessage = 'copied';
        const { result } = renderHook(() => useClipboard());

        await result.current.copy(textToCopy, confirmationMessage);

        expect(mockwriteText).toHaveBeenCalledWith(textToCopy);
        expect(mockAddNotification).toHaveBeenCalledWith({
            message: confirmationMessage,
            type: NOTIFICATION_TYPE.INFO,
        });
    });

    it('Copy and shows a error notification message', async () => {
        mockwriteText.mockRejectedValue(true);
        const textToCopy = 'this is a test';
        const errorMessage = 'error';
        const { result } = renderHook(() => useClipboard());

        await result.current.copy(textToCopy, '', errorMessage);

        expect(mockwriteText).toHaveBeenCalledWith(textToCopy);
        expect(mockAddNotification).toHaveBeenCalledWith({ message: errorMessage, type: NOTIFICATION_TYPE.ERROR });
    });
});
