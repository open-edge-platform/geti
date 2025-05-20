// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useRef } from 'react';

import { View } from '@adobe/react-spectrum';
import { useLoadMore } from '@react-aria/utils';
import {
    ListBox as AriaComponentsListBox,
    ListBoxItem,
    ListLayout,
    ListLayoutOptions,
    Selection,
    Virtualizer,
} from 'react-aria-components';

import { LoadingIndicator } from '../loading/loading-indicator.component';

import classes from './virtualize-list-layout.module.scss';

interface VirtualizedListLayoutProps<T> {
    items: T[];
    selected: Selection;
    isLoading: boolean;
    ariaLabel?: string;
    layoutOptions: ListLayoutOptions;
    renderLoading?: () => ReactNode;
    renderItem: (item: T) => ReactNode;
    onLoadMore: () => void;
}

export const VirtualizedListLayout = <T extends { id: string; name: string }>({
    items,
    isLoading,
    selected,
    ariaLabel,
    layoutOptions,
    renderLoading = () => <LoadingIndicator size={'M'} />,
    renderItem,
    onLoadMore,
}: VirtualizedListLayoutProps<T>) => {
    const ref = useRef<HTMLDivElement | null>(null);
    useLoadMore({ onLoadMore, isLoading, items }, ref);

    return (
        <View UNSAFE_className={classes.mainContainer}>
            <Virtualizer layout={ListLayout} layoutOptions={layoutOptions}>
                <AriaComponentsListBox
                    ref={ref}
                    className={classes.container}
                    selectionMode='single'
                    selectedKeys={selected}
                    aria-label={ariaLabel}
                >
                    {items.map((item) => {
                        return (
                            <ListBoxItem id={item.id} key={item.id} textValue={item.name}>
                                {renderItem(item)}
                            </ListBoxItem>
                        );
                    })}

                    {isLoading && (
                        <ListBoxItem id={'loader'} textValue={'loading'}>
                            {renderLoading()}
                        </ListBoxItem>
                    )}
                </AriaComponentsListBox>
            </Virtualizer>
        </View>
    );
};
