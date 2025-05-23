// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import {
    InfiniteData,
    infiniteQueryOptions,
    QueryKey,
    queryOptions,
    useInfiniteQuery,
    useMutation,
    UseMutationResult,
    useQuery,
    useQueryClient,
    UseQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import QUERY_KEYS from '../../../../packages/core/src/requests/query-keys';
import { getErrorMessage } from '../../../../packages/core/src/services/utils';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { NextPage } from '../../shared/infinite-query.interface';
import { SortDirection } from '../../shared/query-parameters';
import { Organization, OrganizationIdentifier, OrganizationsResponse } from '../organizations.interface';
import { GetOrganizationsQueryOptions, OrganizationsService } from '../services/organizations-service.interface';
import { getOrganizationsQueryOptionsDTO } from '../services/utils';

interface OrganizationInvitationData {
    organizationName: string;
    adminEmail: string;
}

interface UseOrganizationsQuery {
    organizations: Organization[];
    totalCount: number;
    totalMatchedCount: number;
    getNextPage: () => Promise<void>;
    isLoading: boolean;
}

interface UseOrganizationsApi {
    useOrganizationsQuery: (
        queryOptions?: GetOrganizationsQueryOptions
    ) => UseOrganizationsQuery & { isFetchingNextPage: boolean };
    useGetOrganizationQuery: (organizationId: string) => UseQueryResult<Organization, AxiosError>;
    useUpdateOrganizationMutation: () => UseMutationResult<Organization, AxiosError, Organization>;
    useDeleteOrganizationMutation: () => UseMutationResult<void, AxiosError, string>;
    useInviteOrganizationMutation: () => UseMutationResult<void, AxiosError, OrganizationInvitationData>;
}

export const ORGANIZATIONS_QUERY_LIMIT = 20;

export const getOrganizationsQueryOptions = (
    organizationsService: OrganizationsService,
    options: GetOrganizationsQueryOptions = {
        sortBy: 'name',
        sortDirection: SortDirection.ASC,
        limit: ORGANIZATIONS_QUERY_LIMIT,
    }
) => {
    return infiniteQueryOptions<
        OrganizationsResponse,
        AxiosError,
        InfiniteData<OrganizationsResponse>,
        QueryKey,
        NextPage
    >({
        queryKey: QUERY_KEYS.ORGANIZATIONS(options),
        queryFn: ({ pageParam: nextPage = null }) => {
            const nextPageParams = nextPage !== null ? { ...nextPage } : {};

            return organizationsService.getOrganizations(
                getOrganizationsQueryOptionsDTO({ ...options, ...nextPageParams })
            );
        },
        getNextPageParam: ({ nextPage, totalCount }) => {
            if (nextPage === null) {
                return undefined;
            }

            return totalCount > nextPage.skip ? nextPage : undefined;
        },
        getPreviousPageParam: () => undefined,
        staleTime: 1000 * 60,
        meta: { notifyOnError: true },
        initialPageParam: null,
    });
};

export const getOrganizationQueryOptions = (
    organizationsService: OrganizationsService,
    { organizationId }: OrganizationIdentifier
) => {
    return queryOptions<Organization, AxiosError>({
        queryKey: QUERY_KEYS.ORGANIZATION(organizationId),
        queryFn: async () => {
            if (organizationId === undefined) {
                throw new Error('OrganizationID is undefined');
            }

            const { organizations } = await organizationsService.getOrganizations({
                id: organizationId,
            });

            if (organizations.length === 0) {
                throw new Error(`Organization with id ${organizationId} not found`);
            }

            return organizations[0];
        },
    });
};

export const useOrganizationsApi = (): UseOrganizationsApi => {
    const { organizationsService } = useApplicationServices();
    const { addNotification } = useNotification();
    const queryClient = useQueryClient();

    const useOrganizationsQuery = (options: GetOrganizationsQueryOptions = {}) => {
        const { data, isPending, hasNextPage, isFetchingNextPage, fetchNextPage } = useInfiniteQuery(
            getOrganizationsQueryOptions(organizationsService, options)
        );

        const organizations = useMemo(() => data?.pages.flatMap((page) => page.organizations) ?? [], [data?.pages]);
        const totalCount = data?.pages[0].totalCount ?? 0;
        const totalMatchedCount = data?.pages[0].totalMatchedCount ?? 0;

        const getNextPage = async (): Promise<void> => {
            if (hasNextPage && !isFetchingNextPage) {
                await fetchNextPage();
            }
        };

        return {
            organizations,
            totalCount,
            totalMatchedCount,
            getNextPage,
            isLoading: isPending,
            isFetchingNextPage,
        };
    };

    const useGetOrganizationQuery = (organizationId: string) => {
        return useQuery<Organization, AxiosError>({
            ...getOrganizationQueryOptions(organizationsService, { organizationId }),
            meta: { notifyOnError: true },
        });
    };

    const useUpdateOrganizationMutation = (): UseMutationResult<Organization, AxiosError, Organization> => {
        return useMutation({
            mutationFn: organizationsService.updateOrganization,
            onSuccess: async (data) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ORGANIZATIONS({}) });
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ORGANIZATION(data.id) });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    const useDeleteOrganizationMutation = (): UseMutationResult<void, AxiosError, string> => {
        return useMutation({
            mutationFn: organizationsService.deleteOrganization,
            onSuccess: async () => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ORGANIZATIONS({}) });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    const useInviteOrganizationMutation = (): UseMutationResult<void, AxiosError, OrganizationInvitationData> => {
        return useMutation({
            mutationFn: async ({ organizationName, adminEmail }) =>
                await organizationsService.inviteOrganization(organizationName, adminEmail),
        });
    };

    return {
        useOrganizationsQuery,
        useGetOrganizationQuery,
        useUpdateOrganizationMutation,
        useDeleteOrganizationMutation,
        useInviteOrganizationMutation,
    };
};
