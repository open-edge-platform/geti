// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
