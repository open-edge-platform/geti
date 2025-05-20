// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useRef } from 'react';

import { DimensionValue, Responsive, View } from '@geti/ui';
import { useLoadMore } from '@react-aria/utils';
import {
    ListBox as AriaComponentsListBox,
    GridLayout,
    ListBoxItem,
    ListLayout,
    Size,
    Virtualizer,
} from 'react-aria-components';

import { VIEW_MODE_SETTINGS, ViewModes } from '../media-view-modes/utils';
import { useGetTargetPosition } from './use-get-target-position.hook';

import classes from './media-items-list.module.scss';

type ViewModeSettings = Record<ViewModes, { size?: number; gap: number; maxColumns?: number; minItemSize?: number }>;
interface MediaItemsListProps<T> {
    id?: string;
    ariaLabel?: string;
    viewMode: ViewModes;
    mediaItems: T[];
    height?: Responsive<DimensionValue>;
    scrollToIndex?: number;
    viewModeSettings?: ViewModeSettings;
    endReached?: () => void;
    itemContent: (item: T) => ReactNode;
    idFormatter: (item: T) => string;
    getTextValue: (item: T) => string;
}

export const MediaItemsList = <T extends object>({
    id,
    height,
    viewMode,
    mediaItems,
    scrollToIndex,
    ariaLabel = 'media items list',
    viewModeSettings = VIEW_MODE_SETTINGS,
    itemContent,
    endReached,
    idFormatter,
    getTextValue,
}: MediaItemsListProps<T>): JSX.Element => {
    const config = viewModeSettings[viewMode];
    const isDetails = viewMode === ViewModes.DETAILS;
    const layout = isDetails ? 'stack' : 'grid';

    const layoutOptions = isDetails
        ? {
              gap: config.gap,
              rowHeight: config.size,
          }
        : {
              minSpace: new Size(config.gap, config.gap),
              minItemSize: new Size(config.minItemSize, config.minItemSize),
              maxColumns: config.maxColumns,
              preserveAspectRatio: true,
          };

    const ref = useRef<HTMLDivElement | null>(null);
    useLoadMore({ onLoadMore: endReached }, ref);

    const container = ref?.current?.firstElementChild;

    useGetTargetPosition({
        gap: config.gap,
        container,
        targetIndex: scrollToIndex,
        dependencies: [scrollToIndex, viewMode, container],
        callback: (top) => ref.current?.scrollTo({ top, behavior: 'smooth' }),
    });

    return (
        <View id={id} UNSAFE_className={classes.mainContainer} height={height}>
            <Virtualizer layout={isDetails ? ListLayout : GridLayout} layoutOptions={layoutOptions}>
                <AriaComponentsListBox
                    ref={ref}
                    key={layout}
                    layout={layout}
                    aria-label={ariaLabel}
                    className={classes.container}
                >
                    {mediaItems.map((item) => {
                        return (
                            <ListBoxItem
                                id={idFormatter(item)}
                                key={idFormatter(item)}
                                textValue={getTextValue(item)}
                                className={classes.item}
                            >
                                {itemContent(item)}
                            </ListBoxItem>
                        );
                    })}
                </AriaComponentsListBox>
            </Virtualizer>
        </View>
    );
};
