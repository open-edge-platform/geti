// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { RefObject } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';

import type { Media } from '@/api/types';
import { HOTKEYS } from '../../../../shared/hotkeys-definition';

export type UseKeyboardNavigationProps = {
    ref: RefObject<HTMLElement | null>;
    items: Media[];
    selectedIndex: number;
    onSelectedMediaItem: (item: Media) => void;
};

export const useKeyboardNavigation = ({
    ref,
    items,
    selectedIndex,
    onSelectedMediaItem,
}: UseKeyboardNavigationProps) => {
    useHotkeys(
        HOTKEYS.previousMedia,
        (event) => {
            event.preventDefault();
            if (selectedIndex > 0) {
                const newIndex = selectedIndex - 1;
                if (items[newIndex]) {
                    onSelectedMediaItem(items[newIndex]);
                }
            }
        },
        { target: ref },
        [items, selectedIndex, onSelectedMediaItem, ref]
    );

    useHotkeys(
        HOTKEYS.nextMedia,
        (event) => {
            event.preventDefault();
            if (selectedIndex < items.length - 1) {
                const newIndex = selectedIndex + 1;
                if (items[newIndex]) {
                    onSelectedMediaItem(items[newIndex]);
                }
            }
        },
        { target: ref },
        [items, selectedIndex, onSelectedMediaItem, ref]
    );
};
