// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InvalidationContext } from '@react-stately/virtualizer';
import { Key, Layout, LayoutInfo, Rect, Size } from 'react-aria-components';

const DEFAULT_GAP = 8;
const DEFAULT_SIZE = 100;

export interface HorizontalLayoutOptions {
    gap?: number;
    size?: number;
}

export class HorizontalLayout extends Layout {
    protected gap: number;
    protected size: number;

    constructor(options: HorizontalLayoutOptions = {}) {
        super();
        this.gap = options.gap ?? DEFAULT_GAP;
        this.size = options.size ?? DEFAULT_SIZE;
    }

    // Determine which items are visible within the given rectangle.
    getVisibleLayoutInfos(rect: Rect): LayoutInfo[] {
        if (!this.virtualizer) {
            return [];
        }

        const sizeWithGap = this.size + this.gap;
        const keys = Array.from(this.virtualizer.collection.getKeys());
        const startIndex = Math.max(0, Math.floor(rect.x / sizeWithGap));
        const endIndex = Math.min(keys.length - 1, Math.ceil(rect.maxX / sizeWithGap));
        const layoutInfos: LayoutInfo[] = [];

        for (let i = startIndex; i <= endIndex; i++) {
            const layoutInfo = this.getLayoutInfo(keys[i]);
            layoutInfo && layoutInfos.push(layoutInfo);
        }

        // Always add persisted keys (e.g. the focused item), even when out of view.
        for (const key of this.virtualizer.persistedKeys) {
            const item = this.virtualizer.collection.getItem(key);
            const layoutInfo = this.getLayoutInfo(key);
            const isValidItemWithLayoutInfo = item?.index !== undefined && layoutInfo;

            if (isValidItemWithLayoutInfo && item.index < startIndex) {
                layoutInfos.unshift(layoutInfo);
            }
            if (isValidItemWithLayoutInfo && item.index > endIndex) {
                layoutInfos.push(layoutInfo);
            }
        }

        return layoutInfos;
    }

    // Provide a LayoutInfo for a specific item.
    getLayoutInfo(key: Key): LayoutInfo | null {
        const node = this.virtualizer?.collection.getItem(key);
        if (!node) {
            return null;
        }

        const sizeWithGap = this.size + this.gap;
        const rect = new Rect(node.index * sizeWithGap, 0, sizeWithGap, this.size);

        return new LayoutInfo(node.type, node.key, rect);
    }

    // Provide the total size of all items.
    getContentSize(): Size {
        if (!this.virtualizer) {
            return new Size();
        }

        const numItems = this.virtualizer.collection.size;
        const sizeWithGap = this.size + this.gap;

        return new Size(numItems * sizeWithGap, this.size);
    }

    update(invalidationContext: InvalidationContext<HorizontalLayoutOptions>): void {
        this.gap = invalidationContext?.layoutOptions?.gap ?? this.gap;
        this.size = invalidationContext?.layoutOptions?.size ?? this.size;
    }
}
