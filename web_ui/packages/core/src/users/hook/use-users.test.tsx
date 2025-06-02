// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';

import { getMockedUser } from '../../../../../src/test-utils/mocked-items-factory/mocked-users';
import { ApplicationServicesProvider } from '../../services/application-services-provider.component';
import { createInMemoryUsersService } from '../services/in-memory-users-service';
import { useUsers } from './use-users.hook';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({ workspaceId: 'workspace-id', projectId: 'project-id', organizationId: 'organization-123' }),
}));

const mockAddNotification = jest.fn();
jest.mock('../../../../../src/notification/notification.component', () => ({
    ...jest.requireActual('../../../../../src/notification/notification.component'),
    useNotification: () => ({ addNotification: mockAddNotification }),
}));

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: false, // Disable query retries (default is 3)
        },
    },
});

const mockedUser = getMockedUser();
const mockedUsersService = createInMemoryUsersService();
mockedUsersService.getUser = jest.fn(async () => mockedUser);

const wrapper = ({ children }: { children?: ReactNode }) => {
    return (
        <QueryClientProvider client={queryClient}>
            <ApplicationServicesProvider usersService={mockedUsersService} useInMemoryEnvironment>
                {children}
            </ApplicationServicesProvider>
        </QueryClientProvider>
    );
};

describe('useUsers', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('gets activeUser', async () => {
        const { result } = renderHook(() => useUsers(), { wrapper });

        const { result: activeUser } = renderHook(() => result.current.useActiveUser('organization-id'), {
            wrapper,
        });

        await waitFor(() => {
            expect(activeUser.current.data).toStrictEqual(mockedUser);
        });
    });

    it('query is not executed if the user id is "undefined"', async () => {
        const { result } = renderHook(() => useUsers(), { wrapper });

        renderHook(() => result.current.useGetUserQuery('organization-id', undefined), {
            wrapper,
        });

        expect(mockedUsersService.getUser).not.toHaveBeenCalled();
    });

    it('query is not executed if the user id is invalid', async () => {
        const { result } = renderHook(() => useUsers(), { wrapper });

        renderHook(() => result.current.useGetUserQuery('organization-id', 'user@intel.com'), {
            wrapper,
        });

        expect(mockedUsersService.getUser).not.toHaveBeenCalled();
    });
});
