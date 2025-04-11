// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MenuPosition } from '../../../../shared/components/context-menu/context-menu.component';

export enum AnnotationContextMenuItemsKeys {
    EDIT_LABELS = 'Edit labels',
    REMOVE = 'Remove',
    HIDE = 'Hide',
    LOCK = 'Lock',
    UNLOCK = 'Unlock',
    CREATE_STAMP = 'Create stamp',
}

export enum ToolContextMenuItemsKeys {
    CANCEL_STAMP = 'Cancel stamp',
    UNDO = 'Undo',
    REDO = 'Redo',
    FIT_IMAGE = 'Fit image',
    HIDE_ANNOTATIONS = 'Hide annotations',
    SHOW_ANNOTATIONS = 'Show annotations',
}

export const getContextMenuPosition = (
    contextHeight: number,
    contextWidth: number,
    menuPosition: MenuPosition
): MenuPosition => {
    // NOTE: This function is responsible for repositioning of the context menu in case the context menu
    // is either too high or wide and would overlap with footer or go outside the app
    // We use document.getElementById('canvas') because I don't want to create a context only for passing a reference
    // for the canvas element. It's safe to use it.
    const canvasContainerRef = document.getElementById('canvas');
    const canvasBoundingRect = canvasContainerRef?.getBoundingClientRect();

    if (canvasContainerRef == null || canvasBoundingRect == null) {
        return menuPosition;
    }

    const { top, left } = menuPosition;
    const canvasHeight = canvasContainerRef.clientHeight;
    const offsetTop = canvasBoundingRect.top;

    let newLeft: number | null = null;
    let newTop: number | null = null;

    if (contextWidth + left > document.body.clientWidth) {
        newLeft = left - (contextWidth + left - document.body.clientWidth);
    }

    if (contextHeight + top > offsetTop + canvasHeight) {
        newTop = top - (contextHeight + top - offsetTop - canvasHeight);
    }

    if (newLeft !== null || newTop !== null) {
        return {
            left: newLeft ?? left,
            top: newTop ?? top,
        };
    }

    return menuPosition;
};
