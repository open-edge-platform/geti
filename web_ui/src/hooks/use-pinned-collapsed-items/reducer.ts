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

import isEmpty from 'lodash/isEmpty';

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
