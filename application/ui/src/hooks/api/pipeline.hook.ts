// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api, ApiError, fetchClient } from '@/api';
import { PipelineMetrics } from '@/api/types';
import { QueryClient, usePrefetchQuery, useQuery, useQueryClient, useSuspenseQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { getQueryKey } from '../../query-client/query-client';
import { PROJECTS_QUERY_KEY } from './project.hook';

const getPipelineQueryOptions = (projectId: string) => {
    return $api.queryOptions('get', '/api/projects/{project_id}/pipeline', {
        params: {
            path: {
                project_id: projectId,
            },
        },
    });
};

export const usePipeline = () => {
    const projectId = useProjectIdentifier();

    return useSuspenseQuery(getPipelineQueryOptions(projectId));
};

export const usePrefetchPipeline = () => {
    const projectId = useProjectIdentifier();

    return usePrefetchQuery(getPipelineQueryOptions(projectId));
};

export const useProjectPipeline = (projectId: string) => {
    return useQuery({ ...getPipelineQueryOptions(projectId), retry: false });
};

const POLLING_INTERVAL = 5000;
// Aggregate over the polling interval so that consecutive samples do not overlap
const METRICS_TIME_WINDOW_SECONDS = POLLING_INTERVAL / 1000;

// How much metrics history is kept (and displayed) on the client
export const METRICS_HISTORY_WINDOW_MS = 5 * 60 * 1000;

export type MetricsDataPoint = {
    timestamp: number;
    value: number;
};

const getMetricsTimestamp = ({ time_window }: PipelineMetrics): number => new Date(time_window.end).getTime();

const toMetricsData = (metrics: PipelineMetrics[]) => {
    const latencyData: MetricsDataPoint[] = [];
    const throughputData: MetricsDataPoint[] = [];

    metrics.forEach((sample) => {
        const timestamp = getMetricsTimestamp(sample);

        latencyData.push({ timestamp, value: sample.inference.latency.avg_ms ?? 0 });
        throughputData.push({ timestamp, value: sample.inference.throughput.avg_requests_per_second ?? 0 });
    });

    return { latencyData, throughputData };
};

const pipelineMetricsQueryOptions = (projectId: string) => {
    return $api.queryOptions('get', '/api/projects/{project_id}/pipeline/metrics', {
        params: {
            path: { project_id: projectId },
            query: { time_window: METRICS_TIME_WINDOW_SECONDS },
        },
    });
};

export const usePipelineMetrics = () => {
    const projectId = useProjectIdentifier();
    const { queryKey } = pipelineMetricsQueryOptions(projectId);

    return useQuery({
        queryKey,
        queryFn: async ({ client, signal }) => {
            const { data, error } = await fetchClient.GET('/api/projects/{project_id}/pipeline/metrics', {
                ...queryKey[2],
                signal,
            });

            if (error) {
                throw new ApiError(error);
            }

            const previousMetrics = client.getQueryData<PipelineMetrics[]>(queryKey) ?? [];

            if (data === undefined) {
                return previousMetrics;
            }

            const cutoff = getMetricsTimestamp(data) - METRICS_HISTORY_WINDOW_MS;

            return [...previousMetrics, data].filter((sample) => getMetricsTimestamp(sample) > cutoff);
        },
        select: toMetricsData,
        refetchInterval: (query) => (query.state.status === 'success' ? POLLING_INTERVAL : false),
        retry: false,
    });
};

export const usePipelineHealth = () => {
    const projectId = useProjectIdentifier();

    return $api.useQuery(
        'get',
        '/api/projects/{project_id}/pipeline/health',
        {
            params: { path: { project_id: projectId } },
        },
        {
            refetchInterval: POLLING_INTERVAL,
            retry: false,
        }
    );
};

export const usePatchPipeline = () => {
    const queryClient = useQueryClient();

    return $api.useMutation('patch', '/api/projects/{project_id}/pipeline', {
        onSuccess: (
            _,
            {
                params: {
                    path: { project_id },
                },
            }
        ) => {
            return queryClient.invalidateQueries({
                queryKey: getQueryKey([
                    'get',
                    '/api/projects/{project_id}/pipeline',
                    { params: { path: { project_id } } },
                ]),
            });
        },
    });
};

const invalidatePipelineAndProjects = (queryClient: QueryClient, project_id: string) =>
    Promise.all([
        queryClient.invalidateQueries({
            queryKey: getQueryKey(['get', '/api/projects/{project_id}/pipeline', { params: { path: { project_id } } }]),
        }),
        queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY }),
    ]);

export const useEnablePipeline = () => {
    const queryClient = useQueryClient();

    return $api.useMutation('post', '/api/projects/{project_id}/pipeline:enable', {
        onSuccess: (
            _,
            {
                params: {
                    path: { project_id },
                },
            }
        ) => invalidatePipelineAndProjects(queryClient, project_id),
    });
};

export const useDisablePipeline = () => {
    const queryClient = useQueryClient();

    return $api.useMutation('post', '/api/projects/{project_id}/pipeline:disable', {
        onSuccess: (
            _,
            {
                params: {
                    path: { project_id },
                },
            }
        ) => invalidatePipelineAndProjects(queryClient, project_id),
    });
};

export const useCapturePipelineFrame = () => {
    return $api.useMutation('post', '/api/projects/{project_id}/pipeline:capture');
};

export const useConnectSourceToPipeline = () => {
    const project_id = useProjectIdentifier();
    const pipeline = usePatchPipeline();

    return (source_id: string) => pipeline.mutateAsync({ params: { path: { project_id } }, body: { source_id } });
};

export const useConnectSinkToPipeline = () => {
    const project_id = useProjectIdentifier();
    const pipeline = usePatchPipeline();

    return (sink_id: string) => pipeline.mutateAsync({ params: { path: { project_id } }, body: { sink_id } });
};
