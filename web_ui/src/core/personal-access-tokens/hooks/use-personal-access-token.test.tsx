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

import { waitFor } from '@testing-library/react';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import {
    DELETE_MESSAGE,
    RETRIEVE_ERROR,
    UPDATE_MESSAGE,
    usePersonalAccessToken,
} from './use-personal-access-token.hook';

const mockInvalidateQueries = jest.fn();
jest.mock('@tanstack/react-query', () => ({
    ...jest.requireActual('@tanstack/react-query'),
    useQueryClient: () => ({
        invalidateQueries: mockInvalidateQueries,
    }),
}));

const mockCreatePersonalAccessToken = jest.fn();
const mockDeletePersonalAccessToken = jest.fn();
const mockUpdatePersonalAccessToken = jest.fn();
jest.mock('../../../core/personal-access-tokens/in-memory-personal-access-tokens-service', () => ({
    ...jest.requireActual('../../../core/personal-access-tokens/in-memory-personal-access-tokens-service'),
    createInMemoryPersonalAccessTokensService: () => ({
        createPersonalAccessToken: mockCreatePersonalAccessToken,
        deletePersonalAccessToken: mockDeletePersonalAccessToken,
        updatePersonalAccessToken: mockUpdatePersonalAccessToken,
    }),
}));

const mockAddNotification = jest.fn();
jest.mock('../../../notification/notification.component', () => ({
    ...jest.requireActual('../../../notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

const renderPersonalAccessTokenHook = () => {
    return renderHookWithProviders(() => usePersonalAccessToken());
};

describe('usePersonalAccessToken', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterAll(() => {
        jest.clearAllMocks();
    });

    describe('createPersonalAccessToken', () => {
        it('Successfully created personal access token', async () => {
            const { result } = renderPersonalAccessTokenHook();

            result.current.createPersonalAccessTokenMutation.mutate({
                name: 'some name',
                description: 'some desc',
                expirationDate: '10/10/2020',
                organizationId: '1',
                userId: '1',
            });

            await waitFor(() => {
                expect(mockInvalidateQueries).toHaveBeenCalled();
            });
        });

        it('Copy and shows a error notification message', async () => {
            const errorMessage = 'error test';
            mockCreatePersonalAccessToken.mockRejectedValue({ message: errorMessage });

            const { result } = renderPersonalAccessTokenHook();

            result.current.createPersonalAccessTokenMutation.mutate({
                name: 'some name',
                description: 'some desc',
                expirationDate: '10/10/2020',
                organizationId: '1',
                userId: '1',
            });

            await waitFor(() => {
                expect(mockInvalidateQueries).not.toHaveBeenCalled();
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: errorMessage,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });

        it('Copy and shows a default error  notification message', async () => {
            mockCreatePersonalAccessToken.mockRejectedValue(false);
            const { result } = renderPersonalAccessTokenHook();

            result.current.createPersonalAccessTokenMutation.mutate({
                name: 'some name',
                description: 'some desc',
                expirationDate: '10/10/2020',
                organizationId: '',
                userId: '',
            });
            await waitFor(() => {
                expect(mockInvalidateQueries).not.toHaveBeenCalled();
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: RETRIEVE_ERROR,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });
    });

    describe('deletePersonalAccessTokenMutation', () => {
        it('successfully delted personal access token', async () => {
            const { result } = renderPersonalAccessTokenHook();

            await result.current.deletePersonalAccessTokenMutation.mutate({
                organizationId: '1',
                userId: '1',
                tokenId: '1',
            });
            await waitFor(() => {
                expect(mockInvalidateQueries).toHaveBeenCalled();
            });
        });

        it('shows error message', async () => {
            const errorMessage = 'error test';
            mockDeletePersonalAccessToken.mockRejectedValue({ message: errorMessage });
            const { result } = renderPersonalAccessTokenHook();

            await result.current.deletePersonalAccessTokenMutation.mutate({
                organizationId: '1',
                userId: '1',
                tokenId: '1',
            });
            await waitFor(() => {
                expect(mockInvalidateQueries).not.toHaveBeenCalled();
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: errorMessage,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });

        it('shows a default error message', async () => {
            mockDeletePersonalAccessToken.mockRejectedValue(false);
            const { result } = renderPersonalAccessTokenHook();

            await result.current.deletePersonalAccessTokenMutation.mutate({
                organizationId: '1',
                userId: '1',
                tokenId: '1',
            });
            await waitFor(() => {
                expect(mockInvalidateQueries).not.toHaveBeenCalled();
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: DELETE_MESSAGE,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });
    });

    describe('updatePersonalAccessTokenMutation', () => {
        it('successfully updated personal access token', async () => {
            const { result } = renderPersonalAccessTokenHook();

            await result.current.updatePersonalAccessTokenMutation.mutate({
                organizationId: '1',
                userId: '1',
                tokenId: '1',
                expirationDate: '10/10/2020',
            });
            await waitFor(() => {
                expect(mockInvalidateQueries).toHaveBeenCalled();
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: UPDATE_MESSAGE,
                    type: NOTIFICATION_TYPE.DEFAULT,
                });
            });
        });

        it('shows error message', async () => {
            const errorMessage = 'error test';
            mockUpdatePersonalAccessToken.mockRejectedValue({ message: errorMessage });
            const { result } = renderPersonalAccessTokenHook();

            await result.current.updatePersonalAccessTokenMutation.mutate({
                organizationId: '1',
                userId: '1',
                tokenId: '1',
                expirationDate: '10/10/2020',
            });
            await waitFor(() => {
                expect(mockInvalidateQueries).not.toHaveBeenCalled();
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: errorMessage,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });

        it('shows a default error message', async () => {
            mockUpdatePersonalAccessToken.mockRejectedValue(false);
            const { result } = renderPersonalAccessTokenHook();

            await result.current.updatePersonalAccessTokenMutation.mutate({
                organizationId: '1',
                userId: '1',
                tokenId: '1',
                expirationDate: '10/10/2020',
            });
            await waitFor(() => {
                expect(mockInvalidateQueries).not.toHaveBeenCalled();
                expect(mockAddNotification).toHaveBeenCalledWith({
                    message: DELETE_MESSAGE,
                    type: NOTIFICATION_TYPE.ERROR,
                });
            });
        });
    });
});
