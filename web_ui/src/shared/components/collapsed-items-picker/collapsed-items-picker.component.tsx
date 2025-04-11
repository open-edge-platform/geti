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
