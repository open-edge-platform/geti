// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dataset } from '../../core/projects/dataset.interface';
import { WorkspaceEntity } from '../../core/workspaces/services/workspaces.interface';

export interface PinnedCollapsedItems<Entity extends Dataset | WorkspaceEntity> {
    pinnedItems: Entity[];
    collapsedItems: Entity[];
}

export enum PinnedCollapsedItemsAction {
    /* creates a new item, if we do not have enough pinned items, we push it to the pinned,
       if we have reached a limit of the pinned items, we move last pinned item to collapsed and the newly created
       item is placed at the end of pinned items */
    CREATE = 'CREATE',

    /* removes an item, we can only remove item from pinned so if we have any item in collapsed items
       we want to move it to the end of pinned items */
    REMOVE = 'REMOVE',

    /* updates name of item */
    UPDATE = 'UPDATE',

    /* we have to check if selected item in collapsed items, if yes we have to swap last pinned item
       with selected one */
    SWAP = 'SWAP',
}

export type PinnedCollapsedItemsActions<Entity extends Dataset | WorkspaceEntity> =
    | { type: PinnedCollapsedItemsAction.REMOVE; payload: { id: string } }
    | { type: PinnedCollapsedItemsAction.UPDATE; payload: { id: string; name: string } }
    | { type: PinnedCollapsedItemsAction.CREATE; payload: Entity }
    | { type: PinnedCollapsedItemsAction.SWAP; payload: { id: string } };
