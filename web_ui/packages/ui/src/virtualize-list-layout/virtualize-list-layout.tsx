// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useRef } from 'react';

import { DimensionValue, View } from '@adobe/react-spectrum';
import { useLoadMore } from '@react-aria/utils';
import { type Responsive } from '@react-types/shared';
import {
    ListBox as AriaComponentsListBox,
    ListBoxItem,
    ListLayout,
    ListLayoutOptions,
    Selection,
    Virtualizer,
} from 'react-aria-components';

import { Loading } from '../loading/loading.component';

import classes from './virtualize-list-layout.module.scss';

interface VirtualizedListLayoutProps<T> {
    items: T[];
    selected?: Selection;
    isLoading?: boolean;
    ariaLabel?: string;
    layoutOptions: ListLayoutOptions;
    containerHeight?: Responsive<DimensionValue>;
    onLoadMore?: () => void;
    renderLoading?: () => ReactNode;
    renderItem: (item: T) => ReactNode;
    idFormatter: (item: T) => string;
    textValueFormatter: (item: T) => string;
}

export const VirtualizedListLayout = <T,>({
    items,
    isLoading,
    selected,
    ariaLabel,
    layoutOptions,
    containerHeight,
    renderLoading = () => <Loading mode='inline' size={'M'} />,
    renderItem,
    onLoadMore,
    idFormatter,
    textValueFormatter,
}: VirtualizedListLayoutProps<T>) => {
    const ref = useRef<HTMLDivElement | null>(null);
    useLoadMore({ onLoadMore, isLoading, items }, ref);

    return (
        <View UNSAFE_className={classes.mainContainer} height={containerHeight}>
            <Virtualizer layout={ListLayout} layoutOptions={layoutOptions}>
                <AriaComponentsListBox
                    ref={ref}
                    className={classes.container}
                    selectionMode='single'
                    selectedKeys={selected}
                    aria-label={ariaLabel}
                >
                    {items.map((item) => {
                        const id = idFormatter(item);

                        return (
                            <ListBoxItem id={id} key={id} textValue={textValueFormatter(item)}>
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
