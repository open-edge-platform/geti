// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty } from 'lodash-es';

import { Dataset } from '../../core/projects/dataset.interface';
import { WorkspaceEntity } from '../../core/workspaces/services/workspaces.interface';
import { hasDifferentId, hasEqualId } from '../../shared/utils';
import {
    PinnedCollapsedItems,
    PinnedCollapsedItemsAction,
    PinnedCollapsedItemsActions,
} from './use-pinned-collapsed-items.interface';

export const pinnedCollapsedReducer =
    <Entity extends Dataset | WorkspaceEntity>(maxNumberOfDisplayedItems: number) =>
    (
        state: PinnedCollapsedItems<Entity>,
        action: PinnedCollapsedItemsActions<Entity>
    ): PinnedCollapsedItems<Entity> => {
        switch (action.type) {
            case PinnedCollapsedItemsAction.CREATE: {
                const { pinnedItems, collapsedItems } = state;
                const dataset = action.payload;

                if (pinnedItems.length < maxNumberOfDisplayedItems) {
                    return {
                        pinnedItems: [...pinnedItems, dataset],
                        collapsedItems,
                    };
                }

                const lastPinnedDataset = pinnedItems[pinnedItems.length - 1];

                return {
                    pinnedItems: [...pinnedItems, dataset].filter(hasDifferentId(lastPinnedDataset.id)),
                    collapsedItems: [lastPinnedDataset, ...collapsedItems],
                };
            }
            case PinnedCollapsedItemsAction.UPDATE: {
                const { pinnedItems, collapsedItems } = state;
                const { id, name } = action.payload;

                return {
                    pinnedItems: pinnedItems.map((dataset) => (dataset.id == id ? { ...dataset, name } : dataset)),
                    collapsedItems,
                };
            }
            case PinnedCollapsedItemsAction.REMOVE: {
                const { pinnedItems, collapsedItems } = state;

                const firstDatasetFromCollapsed = !isEmpty(collapsedItems) ? collapsedItems[0] : null;
                const filteredOutPinnedDatasets = pinnedItems.filter(hasDifferentId(action.payload.id));

                if (firstDatasetFromCollapsed) {
                    const filteredOutCollapsedDatasets = collapsedItems.filter(
                        hasDifferentId(firstDatasetFromCollapsed.id)
                    );

                    return {
                        pinnedItems: [...filteredOutPinnedDatasets, firstDatasetFromCollapsed],
                        collapsedItems: filteredOutCollapsedDatasets,
                    };
                }

                return {
                    pinnedItems: filteredOutPinnedDatasets,
                    collapsedItems,
                };
            }
            case PinnedCollapsedItemsAction.SWAP: {
                const { pinnedItems, collapsedItems } = state;

                const selectedDatasetFromCollapsed = collapsedItems.find(hasEqualId(action.payload.id));
                const lastPinnedDataset = pinnedItems[pinnedItems.length - 1];

                // this condition never should be true, it's for type safety
                if (!selectedDatasetFromCollapsed || !lastPinnedDataset) return state;

                return {
                    pinnedItems: [...pinnedItems, selectedDatasetFromCollapsed].filter(
                        hasDifferentId(lastPinnedDataset.id)
                    ),
                    collapsedItems: [lastPinnedDataset, ...collapsedItems].filter(
                        hasDifferentId(selectedDatasetFromCollapsed.id)
                    ),
                };
            }
        }
    };
