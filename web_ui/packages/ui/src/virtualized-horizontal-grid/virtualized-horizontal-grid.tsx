// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { DimensionValue, View } from '@adobe/react-spectrum';
import { type Responsive } from '@react-types/shared';
import { ListBox as AriaComponentsListBox, ListBoxItem, Virtualizer } from 'react-aria-components';

import { HorizontalLayout, HorizontalLayoutOptions } from './horizontal-layout';

import classes from './virtualized-horizontal-grid.module.scss';

interface VirtualizedHorizontalGridProps<T> {
    items: T[];
    size: number;
    containerHeight?: Responsive<DimensionValue>;
    renderItem: (item: T) => ReactNode;
    idFormatter: (item: T) => string;
    textValueFormatter: (item: T) => string;
}

export const VirtualizedHorizontalGrid = <T,>({
    size,
    items,
    containerHeight,
    renderItem,
    idFormatter,
    textValueFormatter,
}: VirtualizedHorizontalGridProps<T>) => {
    return (
        <View position={'relative'} width={'100%'} height={`calc(${containerHeight} + 1px)`}>
            <Virtualizer<HorizontalLayoutOptions> layout={HorizontalLayout} layoutOptions={{ size, gap: 4 }}>
                <AriaComponentsListBox className={classes.container} orientation='horizontal'>
                    {items.map((item) => {
                        const id = idFormatter(item);

                        return (
                            <ListBoxItem id={id} key={id} textValue={textValueFormatter(item)}>
                                {renderItem(item)}
                            </ListBoxItem>
                        );
                    })}
                </AriaComponentsListBox>
            </Virtualizer>
        </View>
    );
};
