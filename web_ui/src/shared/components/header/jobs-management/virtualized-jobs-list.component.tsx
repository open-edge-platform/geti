// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useRef } from 'react';

import { View } from '@geti/ui';
import { useLoadMore } from '@react-aria/utils';
import {
    ListBox as AriaComponentsListBox,
    ListBoxItem,
    ListLayout,
    Selection,
    Virtualizer,
} from 'react-aria-components';

import { Job } from '../../../../core/jobs/jobs.interface';

import classes from './jobs.module.scss';

interface VirtualizedJobListProps {
    items: Job[];
    gap: number;
    isLoading: boolean;
    selected: Selection;
    onLoadMore: () => void;
    children: (item: Job) => ReactNode;
}

export const VirtualizedJobList = ({
    gap,
    items,
    isLoading,
    selected,
    children,
    onLoadMore,
}: VirtualizedJobListProps) => {
    const ref = useRef<HTMLDivElement | null>(null);
    useLoadMore({ onLoadMore, isLoading, items }, ref);

    return (
        <View UNSAFE_className={classes.mainContainer}>
            <Virtualizer layout={ListLayout} layoutOptions={{ gap }}>
                <AriaComponentsListBox
                    ref={ref}
                    className={classes.container}
                    selectionMode='single'
                    selectedKeys={selected}
                >
                    {items.map((job) => {
                        return (
                            <ListBoxItem id={job.id} key={job.id} textValue={job.name}>
                                {children(job)}
                            </ListBoxItem>
                        );
                    })}
                </AriaComponentsListBox>
            </Virtualizer>
        </View>
    );
};
