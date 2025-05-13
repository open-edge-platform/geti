// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useRef } from 'react';

import { View } from '@adobe/react-spectrum';
import { useLoadMore } from '@react-aria/utils';
import clsx from 'clsx';
import {
    ListBox as AriaComponentsListBox,
    GridLayout,
    ListBoxItem,
    ListLayout,
    Size,
    Virtualizer,
} from 'react-aria-components';

import { ViewModes } from '../media-view-modes/utils';

import classes from './media-items-list.module.scss';

type ViewModeSettings = Record<ViewModes, { size?: number; gap: number; maxColumns?: number; minItemSize?: number }>;
interface MediaItemsListProps<T> {
    id?: string;
    ariaLabel?: string;
    viewMode: ViewModes;
    endReached: () => void;
    itemContent: (item: T) => ReactNode;
    idFormatter: (item: T) => string;
    mediaItems: T[];
    viewModeSettings: ViewModeSettings;
}

export const MediaItemsList = <T,>({
    id,
    viewMode,
    ariaLabel,
    mediaItems,
    viewModeSettings,
    itemContent,
    endReached,
    idFormatter,
}: MediaItemsListProps<T>): JSX.Element => {
    const config = viewModeSettings[viewMode];
    const isDetails = viewMode === ViewModes.DETAILS;
    const formattedMediaItems = mediaItems?.map((item) => ({ id: idFormatter(item), ...item })) ?? [];

    const ref = useRef(null);
    useLoadMore({ onLoadMore: endReached }, ref);

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

    return (
        <View id={id} UNSAFE_className={classes.mainContainer}>
            <Virtualizer layout={isDetails ? ListLayout : GridLayout} layoutOptions={layoutOptions}>
                <AriaComponentsListBox
                    ref={ref}
                    layout={isDetails ? 'stack' : 'grid'}
                    aria-label={ariaLabel}
                    items={formattedMediaItems}
                    className={clsx(classes.container)}
                >
                    {(item) => (
                        <ListBoxItem textValue={item.id} style={{ background: 'green', height: '100%' }}>
                            {itemContent(item)}
                        </ListBoxItem>
                    )}
                </AriaComponentsListBox>
            </Virtualizer>
        </View>
    );
};
