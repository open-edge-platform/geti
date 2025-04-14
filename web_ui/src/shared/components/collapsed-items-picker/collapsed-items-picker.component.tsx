// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Item, Picker } from '@adobe/react-spectrum';

import classes from './collapsed-items-picker.module.scss';

interface CollapsedItemsPickerProps {
    hasSelectedPinnedItem: boolean;
    numberOfCollapsedItems: number;
    onSelectionChange: (key: string) => void;
    items: { id: string; name: string }[];
    ariaLabel: string;
}

export const CollapsedItemsPicker = ({
    items,
    ariaLabel,
    onSelectionChange,
    hasSelectedPinnedItem,
    numberOfCollapsedItems,
}: CollapsedItemsPickerProps): JSX.Element => {
    return (
        <Picker
            isQuiet
            items={items}
            UNSAFE_className={[classes.collapsedItemsPicker, !hasSelectedPinnedItem ? classes.selected : ''].join(' ')}
            aria-label={ariaLabel}
            placeholder={`${numberOfCollapsedItems} more`}
            onSelectionChange={(key: Key) => onSelectionChange(String(key))}
        >
            {(item) => <Item>{item.name}</Item>}
        </Picker>
    );
};
