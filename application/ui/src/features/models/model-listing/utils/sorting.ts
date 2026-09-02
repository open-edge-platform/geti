// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { DatasetRevision, Model } from '@/api/types';
import dayjs from 'dayjs';
import { orderBy } from 'lodash-es';

import { getTestingMetric } from '../components/model-row/utils';
import type { GroupedModels, SortBy, SortDirection } from '../types';

export const DEFAULT_SORT_DIRECTIONS: Record<SortBy, SortDirection> = {
    name: 'asc',
    trained: 'desc',
    architecture: 'asc',
    dataset: 'desc',
    device: 'asc',
    size: 'asc',
    score: 'desc',
};

export const sortModels = (
    models: Model[],
    sortBy: SortBy,
    datasetRevisions: DatasetRevision[],
    direction: SortDirection = DEFAULT_SORT_DIRECTIONS[sortBy]
): Model[] => {
    switch (sortBy) {
        case 'name':
            return orderBy(models, (model) => model.name.toLowerCase(), direction);
        case 'architecture':
            return orderBy(models, (model) => model.architecture?.toLowerCase() ?? '', direction);
        case 'trained':
            return orderBy(
                models,
                [
                    // Models without a valid training date come last in both directions.
                    (model) => (dayjs(model.training_info?.end_time).isValid() ? 0 : 1),
                    (model) => {
                        const date = dayjs(model.training_info?.end_time);

                        return date.isValid() ? date.valueOf() : 0;
                    },
                ],
                ['asc', direction]
            );
        case 'device':
            return orderBy(
                models,
                [
                    // Models without a device come last.
                    (model) => (model.training_info?.device?.name != null ? 0 : 1),
                    (model) => model.training_info?.device?.name?.toLowerCase() ?? '',
                ],
                ['asc', direction]
            );
        case 'size':
            return orderBy(models, (model) => model.size ?? 0, direction);
        case 'score':
            return orderBy(
                models,
                [
                    // Models without a score come last.
                    (model) => (getTestingMetric(model) !== undefined ? 0 : 1),
                    (model) => getTestingMetric(model)?.value ?? 0,
                ],
                ['asc', direction]
            );
        case 'dataset': {
            const datasetRevisionsMap = new Map(
                datasetRevisions.map((datasetRevision) => [datasetRevision.id, datasetRevision])
            );

            const getDatasetRevision = (model: Model) => {
                const id = model.training_info?.dataset_revision_id;
                return id != null ? datasetRevisionsMap.get(id) : undefined;
            };

            return orderBy(
                models,
                [
                    // First: models without a resolvable dataset revision come last.
                    (model) => (getDatasetRevision(model) != null ? 0 : 1),
                    // Second: sort by dataset revision creation date.
                    (model) => {
                        const createdAt = getDatasetRevision(model)?.created_at;

                        return createdAt ?? '';
                    },
                    // Third: sort by dataset revision name.
                    (model) => getDatasetRevision(model)?.name?.toLowerCase() ?? '',
                ],
                ['asc', direction, direction]
            );
        }
        default:
            console.error(`Unknown sort option: ${sortBy satisfies never}`);
            return models;
    }
};

export const sortGroupedModelsByDatasetRevisionDate = (
    groupedModels: GroupedModels[],
    datasetRevisions: DatasetRevision[]
): GroupedModels[] => {
    const datasetRevisionsMap = new Map(
        datasetRevisions.map((datasetRevision) => [datasetRevision.id, datasetRevision])
    );

    return orderBy(
        groupedModels,
        (group) => {
            const mostRecentModel = sortModels(group.models, 'dataset', datasetRevisions)?.at(0);
            const modelDatasetRevisionId = mostRecentModel?.training_info?.dataset_revision_id;
            const datasetRevisionDate =
                modelDatasetRevisionId != null ? datasetRevisionsMap.get(modelDatasetRevisionId)?.created_at : null;

            return datasetRevisionDate ?? '';
        },
        'desc'
    );
};
