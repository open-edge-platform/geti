// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button } from '@geti-ui/ui';
import { useQueryClient } from '@tanstack/react-query';
import { ENTIRE_DATASET_VIEW_ID, useDatasetViewId } from 'hooks/use-dataset-view-id.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEmpty } from 'lodash-es';

import { getQueryKey } from '../../../../../../query-client/query-client';
import { useUnassignMediaFromViewMutation } from '../api/use-unassign-media-from-view';

const useUnassignMediaFromView = () => {
    const projectId = useProjectIdentifier();
    const queryClient = useQueryClient();
    const unassignFromViewMutation = useUnassignMediaFromViewMutation();

    const unassignMediaFromView = (datasetViewId: string, selectedMediaIds: string[]) => {
        if (datasetViewId === ENTIRE_DATASET_VIEW_ID) {
            return;
        }

        unassignFromViewMutation.mutate(
            {
                params: {
                    path: {
                        project_id: projectId,
                        dataset_view_id: datasetViewId,
                    },
                },
                body: {
                    media_ids: selectedMediaIds,
                },
            },
            {
                onSuccess: async () => {
                    await Promise.all([
                        queryClient.invalidateQueries({
                            queryKey: getQueryKey([
                                'get',
                                '/api/projects/{project_id}/dataset/views/{dataset_view_id}/media',
                                { params: { path: { project_id: projectId, dataset_view_id: datasetViewId } } },
                            ]),
                        }),
                        queryClient.invalidateQueries({
                            queryKey: getQueryKey([
                                'get',
                                '/api/projects/{project_id}/dataset/media',
                                { params: { path: { project_id: projectId } } },
                            ]),
                        }),
                        queryClient.invalidateQueries({
                            queryKey: getQueryKey([
                                'get',
                                '/api/projects/{project_id}/dataset/items',
                                { params: { path: { project_id: projectId } } },
                            ]),
                        }),
                    ]);
                },
            }
        );
    };

    return {
        unassignMediaFromView,
        isPending: unassignFromViewMutation.isPending,
    };
};

type UnassignMediaButtonFromViewProps = {
    selectedMediaIds: string[];
    datasetViewId: string;
};

const UnassignMediaButton = ({ selectedMediaIds, datasetViewId }: UnassignMediaButtonFromViewProps) => {
    const { unassignMediaFromView, isPending } = useUnassignMediaFromView();

    const unassignMedia = async () => {
        if (datasetViewId === ENTIRE_DATASET_VIEW_ID) {
            return;
        }

        unassignMediaFromView(datasetViewId, selectedMediaIds);
    };

    return (
        <Button variant={'primary'} onPress={unassignMedia} isPending={isPending}>
            Unassign from this view
        </Button>
    );
};

type UnassignMediaFromViewProps = {
    selectedMediaIds: string[];
};

export const UnassignMediaFromView = ({ selectedMediaIds }: UnassignMediaFromViewProps) => {
    const [datasetViewId] = useDatasetViewId();

    if (isEmpty(selectedMediaIds)) {
        return null;
    }

    if (datasetViewId === ENTIRE_DATASET_VIEW_ID) {
        return null;
    }

    return <UnassignMediaButton selectedMediaIds={selectedMediaIds} datasetViewId={datasetViewId} />;
};
