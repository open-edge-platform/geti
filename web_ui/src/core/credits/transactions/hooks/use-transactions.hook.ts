// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import {
    InfiniteData,
    QueryKey,
    useInfiniteQuery,
    UseInfiniteQueryResult,
    useQuery,
    UseQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { useProjectActions } from '../../../projects/hooks/use-project-actions.hook';
import QUERY_KEYS from '../../../requests/query-keys';
import { useApplicationServices } from '../../../services/application-services-provider.component';
import { NextPage } from '../../../shared/infinite-query.interface';
import { WorkspaceIdentifier } from '../../../workspaces/services/workspaces.interface';
import {
    GetTransactionsAggregatesQueryOptions,
    GetTransactionsQueryOptions,
} from '../services/transactions-service.interface';
import { Transaction, TransactionsAggregatesResponse, TransactionsResponse } from '../transactions.interface';
import { setTransactionAggregatesProjectName, setTransactionProjectName } from './utils';

type UseTransactionsQueryResult = Omit<UseInfiniteQueryResult, 'data' | 'fetchNextPage'> & {
    transactions: Transaction[];
    totalMatched: number;
    getNextPage: () => Promise<void>;
};

interface UseTransactionsQueries {
    useGetTransactions: (
        workspaceId: WorkspaceIdentifier,
        options: GetTransactionsQueryOptions
    ) => UseTransactionsQueryResult;
    useGetTransactionsAggregates: (
        workspaceId: WorkspaceIdentifier,
        options: GetTransactionsAggregatesQueryOptions
    ) => UseQueryResult<TransactionsAggregatesResponse>;
}

export const useTransactionsQueries = (): UseTransactionsQueries => {
    const { useGetProjectNames } = useProjectActions();

    const useGetTransactions = (
        workspaceId: WorkspaceIdentifier,
        options: Omit<GetTransactionsQueryOptions, 'skip'>
    ) => {
        const { transactionsService } = useApplicationServices();
        const { data: projectNames, isPending: isPendingProjectNames } = useGetProjectNames(workspaceId);

        const { data, isFetchingNextPage, hasNextPage, fetchNextPage, ...rest } = useInfiniteQuery<
            TransactionsResponse,
            AxiosError,
            InfiniteData<TransactionsResponse>,
            QueryKey,
            NextPage
        >({
            queryKey: QUERY_KEYS.CREDIT_TRANSACTIONS(workspaceId, options),
            queryFn: async ({ pageParam = {} }) => {
                const { transactions, ...response } = await transactionsService.getTransactions(workspaceId, {
                    ...pageParam,
                    ...options,
                });

                return {
                    ...response,
                    transactions: setTransactionProjectName(projectNames?.projects, transactions),
                };
            },
            meta: { notifyOnError: true },
            getNextPageParam: ({ nextPage }) => nextPage ?? undefined,
            enabled: !isPendingProjectNames,
            initialPageParam: null,
        });

        const transactions = useMemo(() => data?.pages.flatMap((page) => page.transactions) ?? [], [data?.pages]);
        const totalMatched = data?.pages[0]?.totalMatched ?? 0;

        const getNextPage = async () => {
            if (hasNextPage && !isFetchingNextPage) {
                await fetchNextPage();
            }
        };

        return {
            transactions,
            totalMatched,
            hasNextPage,
            isFetchingNextPage,
            getNextPage,
            ...rest,
        };
    };

    const useGetTransactionsAggregates = (
        workspaceId: WorkspaceIdentifier,
        options: GetTransactionsAggregatesQueryOptions
    ) => {
        const { transactionsService } = useApplicationServices();
        const { data: projectNames, isPending: isPendingProjectNames } = useGetProjectNames(workspaceId);

        return useQuery<TransactionsAggregatesResponse, AxiosError>({
            queryKey: QUERY_KEYS.CREDIT_TRANSACTIONS_AGGREGATES(workspaceId, options),
            queryFn: async () => {
                const transactionsAggregatesResponse = await transactionsService.getTransactionsAggregates(
                    workspaceId,
                    options
                );

                return {
                    ...transactionsAggregatesResponse,
                    aggregates: setTransactionAggregatesProjectName(
                        projectNames?.projects,
                        transactionsAggregatesResponse.aggregates
                    ),
                };
            },
            meta: { notifyOnError: true },
            enabled: !isPendingProjectNames,
        });
    };

    return {
        useGetTransactions,
        useGetTransactionsAggregates,
    };
};
