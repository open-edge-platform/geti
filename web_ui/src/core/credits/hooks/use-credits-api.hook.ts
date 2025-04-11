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

import { useMemo } from 'react';

import {
    InfiniteData,
    infiniteQueryOptions,
    QueryKey,
    queryOptions,
    useInfiniteQuery,
    UseInfiniteQueryOptions,
    UseInfiniteQueryResult,
    useMutation,
    UseMutationResult,
    useQuery,
    useQueryClient,
    UseQueryOptions,
    UseQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { OrganizationIdentifier } from '../../organizations/organizations.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import {
    CreditAccount,
    CreditAccountIdentifier,
    CreditAccountsResponse,
    NewCreditAccount,
    NewCreditAccountBalance,
    OrganizationBalance,
} from '../credits.interface';
import { CreditsService, GetCreditAccountsQueryOptions } from '../services/credits-service.interface';

interface UseCreditAccountsQuery {
    creditAccounts: CreditAccount[];
    totalCount: number;
    totalMatchedCount: number;
    hasNextPage?: boolean;
    getNextPage: () => Promise<void>;
    isLoading: UseInfiniteQueryResult<CreditAccountsResponse, AxiosError>['isLoading'];
    isFetchingNextPage: UseInfiniteQueryResult<CreditAccountsResponse, AxiosError>['isFetchingNextPage'];
    status: UseInfiniteQueryResult<CreditAccountsResponse, AxiosError>['status'];
}

interface UpdateCreditAccountBalancePayload {
    id: CreditAccountIdentifier;
    balance: NewCreditAccountBalance;
}

interface UpdateCreditAccountPayload {
    id: CreditAccountIdentifier;
    newCreditAccount: NewCreditAccount;
}
interface UseCreditsQueries {
    useGetOrganizationBalanceQuery: (
        organizationId: OrganizationIdentifier,
        options?: Pick<UseQueryOptions<OrganizationBalance, AxiosError>, 'enabled' | 'refetchInterval'>
    ) => UseQueryResult<OrganizationBalance, AxiosError>;
    useCreditsQuery: (
        organizationId: OrganizationIdentifier,
        options?: Pick<
            UseInfiniteQueryOptions<
                CreditAccountsResponse,
                AxiosError,
                CreditAccountsResponse,
                CreditAccountsResponse,
                QueryKey,
                GetCreditAccountsQueryOptions
            >,
            'enabled'
        >
    ) => UseCreditAccountsQuery;
    useUpdateCreditAccountMutation: () => UseMutationResult<CreditAccount, AxiosError, UpdateCreditAccountPayload>;
    useCreateCreditAccountMutation: () => UseMutationResult<void, AxiosError, NewCreditAccount>;
    useUpdateCreditAccountBalanceMutation: () => UseMutationResult<void, AxiosError, UpdateCreditAccountBalancePayload>;
}

const organizationCreditsBalanceQueryOptions = (
    creditsService: CreditsService,
    organizationId: OrganizationIdentifier
) => {
    return queryOptions<OrganizationBalance, AxiosError>({
        queryKey: QUERY_KEYS.ORGANIZATION_BALANCE(organizationId),
        queryFn: () => creditsService.getOrganizationBalance(organizationId),
    });
};

const organizationCreditAccountsQueryOptions = (
    creditsService: CreditsService,
    organizationId: OrganizationIdentifier
) => {
    return infiniteQueryOptions<
        CreditAccountsResponse,
        AxiosError,
        InfiniteData<CreditAccountsResponse>,
        QueryKey,
        GetCreditAccountsQueryOptions
    >({
        queryKey: QUERY_KEYS.CREDIT_ACCOUNTS(organizationId),
        queryFn: async ({ pageParam = {} }) => creditsService.getCreditAccounts(organizationId, pageParam),
        initialPageParam: {},
        getNextPageParam: ({ nextPage }) => nextPage ?? undefined,
        getPreviousPageParam: () => undefined,
    });
};

export const useCreditsQueries = (): UseCreditsQueries => {
    const queryClient = useQueryClient();
    const { addNotification } = useNotification();
    const { creditsService } = useApplicationServices();

    const useGetOrganizationBalanceQuery: UseCreditsQueries['useGetOrganizationBalanceQuery'] = (
        organizationId,
        options = {}
    ) => {
        return useQuery({
            ...organizationCreditsBalanceQueryOptions(creditsService, organizationId),
            meta: { notifyOnError: true },
            ...options,
        });
    };

    const useCreditsQuery: UseCreditsQueries['useCreditsQuery'] = (
        organizationId,
        options = {}
    ): UseCreditAccountsQuery => {
        const { data, status, isPending, hasNextPage, isFetchingNextPage, fetchNextPage } = useInfiniteQuery({
            ...organizationCreditAccountsQueryOptions(creditsService, organizationId),
            meta: { notifyOnError: true },
            ...options,
        });

        const creditAccounts = useMemo(() => data?.pages.flatMap((page) => page.creditAccounts) ?? [], [data?.pages]);
        const totalCount = data?.pages[0]?.totalCount ?? 0;
        const totalMatchedCount = data?.pages[0]?.totalMatchedCount ?? 0;

        const getNextPage = async () => {
            if (hasNextPage && !isFetchingNextPage) {
                await fetchNextPage();
            }
        };

        return {
            creditAccounts,
            totalCount,
            totalMatchedCount,
            hasNextPage,
            getNextPage,
            isLoading: isPending,
            isFetchingNextPage,
            status,
        };
    };

    const useUpdateCreditAccountMutation = (): UseMutationResult<
        CreditAccount,
        AxiosError,
        UpdateCreditAccountPayload
    > => {
        return useMutation({
            mutationFn: (payload: UpdateCreditAccountPayload) =>
                creditsService.updateCreditAccount(payload.id, payload.newCreditAccount),
            onSuccess: async (data) => {
                await queryClient.invalidateQueries({
                    queryKey: QUERY_KEYS.CREDIT_ACCOUNTS({ organizationId: data.organizationId }),
                });
                addNotification({
                    message: 'Credit account updated successfully',
                    type: NOTIFICATION_TYPE.INFO,
                    dismiss: { duration: 10000 },
                });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    const useCreateCreditAccountMutation = (): UseMutationResult<void, AxiosError, NewCreditAccount> => {
        return useMutation({
            mutationFn: creditsService.createCreditAccount,
            onSuccess: async (_, payload) => {
                await queryClient.invalidateQueries({
                    queryKey: QUERY_KEYS.CREDIT_ACCOUNTS({ organizationId: payload.organizationId }),
                });
                await queryClient.invalidateQueries({
                    queryKey: QUERY_KEYS.ORGANIZATION_BALANCE({ organizationId: payload.organizationId }),
                });
                addNotification({
                    message: 'Credit account created successfully',
                    type: NOTIFICATION_TYPE.INFO,
                    dismiss: { duration: 10 },
                });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    const useUpdateCreditAccountBalanceMutation = (): UseMutationResult<
        void,
        AxiosError,
        UpdateCreditAccountBalancePayload
    > => {
        return useMutation({
            mutationFn: (payload: UpdateCreditAccountBalancePayload) =>
                creditsService.updateCreditAccountBalance(payload.id, payload.balance),
            onSuccess: async (_, payload) => {
                await queryClient.invalidateQueries({
                    queryKey: QUERY_KEYS.CREDIT_ACCOUNTS(payload.id),
                });
                await queryClient.invalidateQueries({
                    queryKey: QUERY_KEYS.ORGANIZATION_BALANCE(payload.id),
                });
                addNotification({
                    message: 'Credit account balance updated successfully',
                    type: NOTIFICATION_TYPE.INFO,
                    dismiss: { duration: 10000 },
                });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    return {
        useCreditsQuery,
        useGetOrganizationBalanceQuery,
        useUpdateCreditAccountMutation,
        useCreateCreditAccountMutation,
        useUpdateCreditAccountBalanceMutation,
    };
};
