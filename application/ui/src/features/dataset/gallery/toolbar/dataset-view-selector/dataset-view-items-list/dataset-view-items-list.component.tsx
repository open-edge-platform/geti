// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Key, ReactNode } from 'react';

import { ActionButton, Divider, Flex, Heading, Item, Menu, MenuTrigger, View } from '@geti-ui/ui';
import { Delete, MoreMenu } from '@geti-ui/ui/icons';
import { clsx } from 'clsx';
import { isEmpty } from 'lodash-es';

import classes from './dataset-view-items-list.module.scss';

// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export type DatasetView = {
    id: string;
    name: string;
};

type DatasetViewItemContainerProps = {
    datasetView: DatasetView;
    isSelected: boolean;
    onSelectDatasetView: (datasetViewId: string) => void;
    children: ReactNode;
};

const DatasetViewItemContainer = ({
    datasetView,
    isSelected,
    onSelectDatasetView,
    children,
}: DatasetViewItemContainerProps) => {
    return (
        <li aria-label={datasetView.name} onClick={() => onSelectDatasetView(datasetView.id)}>
            <View
                padding={'size-200'}
                borderRadius={'regular'}
                UNSAFE_className={clsx(classes.datasetViewInListItem, {
                    [classes.datasetViewListItemSelected]: isSelected,
                })}
            >
                {children}
            </View>
        </li>
    );
};

type DatasetViewItemProps = {
    datasetView: DatasetView;
    isSelected: boolean;
    onSelectDatasetView: (datasetViewId: string) => void;
    onOpenDeleteConfirmationDialog: (datasetView: DatasetView) => void;
    onOpenEditDialog: (datasetView: DatasetView) => void;
};

const DATASET_VIEW_ITEM_OPTIONS = {
    DELETE: 'Delete',
    EDIT: 'Edit',
};

const DatasetViewItem = ({
    datasetView,
    isSelected,
    onOpenEditDialog,
    onSelectDatasetView,
    onOpenDeleteConfirmationDialog,
}: DatasetViewItemProps) => {
    const handleAction = (key: Key) => {
        if (key === DATASET_VIEW_ITEM_OPTIONS.DELETE) {
            onOpenDeleteConfirmationDialog(datasetView);
        } else if (key === DATASET_VIEW_ITEM_OPTIONS.EDIT) {
            onOpenEditDialog(datasetView);
        }
    };

    return (
        <li aria-label={datasetView.name} onClick={() => onSelectDatasetView(datasetView.id)}>
            <View
                padding={'size-200'}
                borderRadius={'regular'}
                UNSAFE_className={clsx(classes.datasetViewInListItem, {
                    [classes.datasetViewListItemSelected]: isSelected,
                })}
            >
                <Flex minWidth={0} alignItems={'center'} justifyContent={'space-between'}>
                    <Heading UNSAFE_className={classes.datasetViewInList}>{datasetView.name}</Heading>
                    <MenuTrigger>
                        <ActionButton isQuiet aria-label={`Dataset view actions for ${datasetView.name}`}>
                            <MoreMenu />
                        </ActionButton>
                        <Menu onAction={handleAction} aria-label={'Media actions menu'}>
                            <Item key={DATASET_VIEW_ITEM_OPTIONS.EDIT}>Edit</Item>
                            <Item key={DATASET_VIEW_ITEM_OPTIONS.DELETE}>Delete</Item>
                        </Menu>
                    </MenuTrigger>
                </Flex>
            </View>
        </li>
    );
};

type EntireDatasetViewItemProps = {
    datasetView: DatasetView;
    isSelected: boolean;
    onSelectDatasetView: (datasetViewId: string) => void;
};

const EntireDatasetViewItem = ({ datasetView, isSelected, onSelectDatasetView }: EntireDatasetViewItemProps) => {
    return (
        <DatasetViewItemContainer
            datasetView={datasetView}
            isSelected={isSelected}
            onSelectDatasetView={onSelectDatasetView}
        >
            <Heading UNSAFE_className={classes.datasetViewInList}>{datasetView.name}</Heading>
        </DatasetViewItemContainer>
    );
};

type DatasetViewItemsListProps = {
    selectedDatasetViewId: string;
    onOpenDeleteConfirmationDialog: (datasetView: DatasetView) => void;
    entireDatasetView: DatasetView;
    otherDatasetViews: DatasetView[];
    onOpenEditDialog: (datasetView: DatasetView) => void;
    onSelectDatasetView: (datasetViewId: string) => void;
};

export const DatasetViewItemsList = ({
    selectedDatasetViewId,
    entireDatasetView,
    otherDatasetViews,
    onSelectDatasetView,
    onOpenEditDialog,
    onOpenDeleteConfirmationDialog,
}: DatasetViewItemsListProps) => {
    return (
        <ul className={classes.datasetViewsList} aria-label={'Dataset views list'}>
            <EntireDatasetViewItem
                datasetView={entireDatasetView}
                isSelected={selectedDatasetViewId === entireDatasetView.id}
                onSelectDatasetView={onSelectDatasetView}
            />

            {!isEmpty(otherDatasetViews) && <Divider size={'S'} />}

            {otherDatasetViews.map((datasetView) => (
                <DatasetViewItem
                    key={datasetView.id}
                    datasetView={datasetView}
                    isSelected={selectedDatasetViewId === datasetView.id}
                    onSelectDatasetView={onSelectDatasetView}
                    onOpenEditDialog={onOpenEditDialog}
                    onOpenDeleteConfirmationDialog={onOpenDeleteConfirmationDialog}
                />
            ))}
        </ul>
    );
};
