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

import { ComboBox, Item } from '@adobe/react-spectrum';

export interface JobsFilterFieldProps {
    value: string;
    options: { key: string; name: string }[];
    onSelectionChange: (key: Key | null) => void;
    isLoading?: boolean;
    loadMore?: () => void;
    id?: string;
    dataTestId?: string;
    ariaLabel?: string;
}

export const JobsFilterField = ({
    options,
    value,
    onSelectionChange,
    isLoading = false,
    loadMore,
    dataTestId,
    ariaLabel,
    id,
}: JobsFilterFieldProps): JSX.Element => {
    return (
        <ComboBox
            id={id}
            data-testid={dataTestId}
            aria-label={ariaLabel}
            defaultItems={options}
            selectedKey={value}
            isQuiet={false}
            allowsCustomValue={false}
            onSelectionChange={onSelectionChange}
            loadingState={isLoading ? 'loadingMore' : 'idle'}
            onLoadMore={loadMore}
        >
            {(item) => {
                return <Item textValue={item.name}>{item.name}</Item>;
            }}
        </ComboBox>
    );
};
