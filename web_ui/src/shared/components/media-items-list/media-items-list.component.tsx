// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { forwardRef, ReactNode, useMemo } from 'react';

import { View } from '@adobe/react-spectrum';
import { StyleProps } from '@react-types/shared';
import { VirtuosoGrid, VirtuosoGridHandle } from 'react-virtuoso';

import { VIEW_MODE_SETTINGS, ViewModes } from '../media-view-modes/utils';

import classes from './media-items-list.module.scss';

interface MediaItemsListProps extends StyleProps {
    id?: string;
    ariaLabel?: string;
    viewMode: ViewModes;
    totalCount: number;
    endReached: () => void;
    itemContent: (index: number) => ReactNode;
}

// Each thumbnail has approximately 150 pixel height (this differs per resolution
// as well as the large/medium/small thumbnails).
// We want to overscan a few (4) rows of thumbnails so that when the user scrolls
// they won't have to wait for loading the images of the next rows
const OVERSCAN = 150 * 4;

export const MediaItemsList = forwardRef<VirtuosoGridHandle | null, MediaItemsListProps>(
    ({ id, viewMode, totalCount, itemContent, endReached, ariaLabel, ...styleProps }, ref): JSX.Element => {
        const style = useMemo(() => {
            return { ...VIEW_MODE_SETTINGS[viewMode] };
        }, [viewMode]);

        return (
            <View id={id} height={'100%'} width={'100%'} {...styleProps}>
                <VirtuosoGrid
                    aria-label={ariaLabel}
                    ref={ref}
                    totalCount={totalCount}
                    overscan={OVERSCAN}
                    style={style}
                    className={classes.gridListContainer}
                    listClassName={viewMode === ViewModes.DETAILS ? undefined : classes.gridList}
                    itemClassName={viewMode === ViewModes.DETAILS ? undefined : classes.gridItem}
                    itemContent={itemContent}
                    endReached={endReached}
                />
            </View>
        );
    }
);
