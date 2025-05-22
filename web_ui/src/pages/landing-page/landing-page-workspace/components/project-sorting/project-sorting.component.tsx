// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { ActionButton, Item, Menu, MenuTrigger, Text, Tooltip, TooltipTrigger } from '@geti/ui';
import { SortUpDown } from '@geti/ui/icons';

interface SortingOptions<T, K> {
    sortBy: T | K;
    sortDir: 'asc' | 'dsc';
}

interface MenuAction {
    key: string;
    ariaLabel: string;
    text: string;
    action: () => void;
    isSelected: boolean;
}

interface ProjectSortingProps<T, K> {
    nameKey: T;
    dateKey: K;
    sortingOptions: SortingOptions<T, K>;
    setSortingOptions: (options: SortingOptions<T, K>) => void;
}

export const ProjectSorting = <T, K>({
    nameKey,
    dateKey,
    setSortingOptions,
    sortingOptions,
}: ProjectSortingProps<T, K>): JSX.Element => {
    const handlerAction = (key: Key) => {
        const selectedAction = sortingActions.find((action: MenuAction) => action.key === key);
        selectedAction && selectedAction.action();
    };

    const sortingActions: MenuAction[] = [
        {
            key: 'AtoZ',
            ariaLabel: 'sort from A to Z',
            text: 'A to Z',
            action: () => {
                setSortingOptions({ sortBy: nameKey, sortDir: 'asc' });
            },
            isSelected: sortingOptions.sortBy === nameKey && sortingOptions.sortDir === 'asc',
        },
        {
            key: 'ZtoA',
            ariaLabel: 'sort from Z to A',
            text: 'Z to A',
            action: () => {
                setSortingOptions({ sortBy: nameKey, sortDir: 'dsc' });
            },
            isSelected: sortingOptions.sortBy === nameKey && sortingOptions.sortDir === 'dsc',
        },
        {
            key: 'NewestToOldest',
            ariaLabel: 'sort from newest to oldest',
            text: 'Newest to Oldest',
            action: () => {
                setSortingOptions({ sortBy: dateKey, sortDir: 'dsc' });
            },
            isSelected: sortingOptions.sortBy === dateKey && sortingOptions.sortDir === 'dsc',
        },
        {
            key: 'OldestToNewest',
            ariaLabel: 'sort from oldest to newest',
            text: 'Oldest to Newest',
            action: () => {
                setSortingOptions({ sortBy: dateKey, sortDir: 'asc' });
            },
            isSelected: sortingOptions.sortBy === dateKey && sortingOptions.sortDir === 'asc',
        },
    ];

    const selectedKeys = sortingActions.filter(({ isSelected }) => isSelected).map(({ key }) => key);
    return (
        <MenuTrigger>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton isQuiet key={'sort'} aria-label={'Sort'}>
                    <SortUpDown />
                </ActionButton>
                <Tooltip>Sort</Tooltip>
            </TooltipTrigger>

            <Menu onAction={handlerAction} defaultSelectedKeys={selectedKeys}>
                {sortingActions.map((action: MenuAction) => (
                    <Item key={action.key} aria-label={action.ariaLabel} textValue={action.text}>
                        <Text>{action.text}</Text>
                    </Item>
                ))}
            </Menu>
        </MenuTrigger>
    );
};
