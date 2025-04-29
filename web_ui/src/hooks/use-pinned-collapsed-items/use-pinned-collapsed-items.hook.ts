// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
