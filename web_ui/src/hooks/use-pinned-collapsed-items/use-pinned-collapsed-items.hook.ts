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

import { Dispatch, useMemo, useReducer } from 'react';

import { Dataset } from '../../core/projects/dataset.interface';
import { WorkspaceEntity } from '../../core/workspaces/services/workspaces.interface';
import { hasDifferentId, hasEqualId } from '../../shared/utils';
import { pinnedCollapsedReducer } from './reducer';
import { PinnedCollapsedItemsActions } from './use-pinned-collapsed-items.interface';

export const usePinnedCollapsedItems = <Entity extends Dataset | WorkspaceEntity>(
    items: Entity[],
    selectedDatasetId: string,
    maxNumberOfDisplayedItems: number
): [
    pinnedItems: Entity[],
    collapsedItems: Entity[],
    setCollapsedItems: Dispatch<PinnedCollapsedItemsActions<Entity>>,
] => {
    const initialState = useMemo(() => {
        const pinnedItems = items.slice(0, maxNumberOfDisplayedItems);
        const collapsedItems = items.slice(maxNumberOfDisplayedItems);

        const selectedItemInCollapsedItemsIndex = collapsedItems.findIndex(hasEqualId(selectedDatasetId));

        if (selectedItemInCollapsedItemsIndex >= 0) {
            const lastPinnedItem = pinnedItems[pinnedItems.length - 1];
            const selectedItem = collapsedItems[selectedItemInCollapsedItemsIndex];

            if (lastPinnedItem === undefined) {
                return {
                    pinnedItems: [...pinnedItems, selectedItem],
                    collapsedItems: collapsedItems.filter(hasDifferentId(selectedItem.id)),
                };
            }

            return {
                pinnedItems: [...pinnedItems, selectedItem].filter(hasDifferentId(lastPinnedItem?.id)),
                collapsedItems: [lastPinnedItem, ...collapsedItems].filter(hasDifferentId(selectedItem.id)),
            };
        }
        return {
            pinnedItems,
            collapsedItems,
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const [{ pinnedItems, collapsedItems }, dispatch] = useReducer(
        pinnedCollapsedReducer<Entity>(maxNumberOfDisplayedItems),
        initialState
    );

    return [pinnedItems, collapsedItems, dispatch];
};
