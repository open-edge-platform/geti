// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import {
    InfiniteData,
    infiniteQueryOptions,
    QueryKey,
    queryOptions,
    useInfiniteQuery,
    UseInfiniteQueryResult,
    useMutation,
    UseMutationResult,
    useQuery,
    useQueryClient,
    UseQueryResult,
} from '@tanstack/react-query';
import { AxiosError, HttpStatusCode, isAxiosError } from 'axios';

import QUERY_KEYS from '../../../../../packages/core/src/requests/query-keys';
import { getErrorMessage } from '../../../../../packages/core/src/services/utils';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { useFeatureFlags } from '../../../feature-flags/hooks/use-feature-flags.hook';
import { OrganizationIdentifier } from '../../../organizations/organizations.interface';
import { Quota, QuotasResponse } from '../quotas.interface';
import { GetQuotasQueryOptions, SubscriptionsService } from '../services/subscription-service.interface';
import { Subscription } from '../subscription.interface';

type UseOrganizationQuotasInfiniteQueryResult = UseInfiniteQueryResult<InfiniteData<QuotasResponse>, AxiosError> & {
    quotas: QuotasResponse['quotas'];
    totalMatched: number;
    getNextPage: () => void;
};

interface UseSubscriptions {
    useGetActiveSubscriptionQuery: (organizationId: OrganizationIdentifier) => UseQueryResult<Subscription, AxiosError>;
    useGetOrganizationQuotasQuery: (
        organizationId: OrganizationIdentifier,
        options?: GetQuotasQueryOptions
    ) => UseOrganizationQuotasInfiniteQueryResult;
    useUpdateQuotaMutation: () => UseMutationResult<void, AxiosError, Quota>;
}

export const getOrganizationActiveSubscriptionQueryOptions = (
    subscriptionsService: SubscriptionsService,
    organizationId: OrganizationIdentifier
) => {
    return queryOptions<Subscription, AxiosError>({
        queryKey: QUERY_KEYS.ACTIVE_SUBSCRIPTION(organizationId),
        queryFn: () => subscriptionsService.getActiveSubscription(organizationId),
        retry: (failureCount, error) => {
            if (failureCount >= 3) {
                return false;
            }

            if (isAxiosError(error)) {
                return error.response?.status !== HttpStatusCode.NotFound;
            }

            return false;
        },
    });
};

const SERVICE_LIMITS_QUERY_LIMIT = 10;
export const getOrganizationQuotasQueryOptions = (
    subscriptionsService: SubscriptionsService,
    organizationId: OrganizationIdentifier,
    options: GetQuotasQueryOptions = { limit: SERVICE_LIMITS_QUERY_LIMIT }
) => {
    return infiniteQueryOptions<
        QuotasResponse,
        AxiosError,
        InfiniteData<QuotasResponse>,
        QueryKey,
        GetQuotasQueryOptions
    >({
        queryKey: QUERY_KEYS.ORGANIZATION_QUOTAS(organizationId),
        queryFn: async ({ pageParam: nextPage }) => {
            return subscriptionsService.getQuotas(organizationId, {
                ...options,
                ...nextPage,
            });
        },
        initialPageParam: {},
        getNextPageParam: ({ nextPage }) => nextPage ?? null,
        getPreviousPageParam: () => null,
    });
};

export const useSubscriptions = (): UseSubscriptions => {
    const { addNotification } = useNotification();
    const { subscriptionsService } = useApplicationServices();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const queryClient = useQueryClient();

    const useGetActiveSubscriptionQuery = (organizationId: OrganizationIdentifier) => {
        const query = useQuery<Subscription, AxiosError>({
            ...getOrganizationActiveSubscriptionQueryOptions(subscriptionsService, organizationId),
            enabled: FEATURE_FLAG_CREDIT_SYSTEM,
        });

        useEffect(() => {
            if (query.error && query.error.response?.status !== HttpStatusCode.NotFound) {
                addNotification({ message: getErrorMessage(query.error), type: NOTIFICATION_TYPE.ERROR });
            }
        }, [query.error]);

        return query;
    };

    const useGetOrganizationQuotasQuery = (organizationId: OrganizationIdentifier, options?: GetQuotasQueryOptions) => {
        const query = useInfiniteQuery<
            QuotasResponse,
            AxiosError,
            InfiniteData<QuotasResponse>,
            QueryKey,
            GetQuotasQueryOptions
        >({
            ...getOrganizationQuotasQueryOptions(subscriptionsService, organizationId, options),
            enabled: FEATURE_FLAG_CREDIT_SYSTEM,
        });

        useEffect(() => {
            if (query.error) {
                addNotification({ message: getErrorMessage(query.error), type: NOTIFICATION_TYPE.ERROR });
            }
        }, [query.error]);

        const getNextPage = () => {
            if (query.hasNextPage && !query.isFetchingNextPage) {
                query.fetchNextPage();
            }
        };

        const quotas = useMemo(() => query.data?.pages.flatMap((page) => page.quotas) ?? [], [query.data]);
        const totalMatchedCount = query.data?.pages.at(0)?.totalMatched ?? 0;

        return {
            ...query,
            quotas,
            totalMatched: totalMatchedCount,
            getNextPage,
        };
    };

    const useUpdateQuotaMutation = () => {
        return useMutation<void, AxiosError, Quota>({
            mutationFn: subscriptionsService.updateQuota,
            onSuccess: async (_data, variables) => {
                await queryClient.invalidateQueries({
                    queryKey: QUERY_KEYS.ORGANIZATION_QUOTAS({ organizationId: variables.organizationId }),
                });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    return {
        useGetActiveSubscriptionQuery,
        useGetOrganizationQuotasQuery,
        useUpdateQuotaMutation,
    };
};
