// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { ActionButton, Divider, Flex, Heading, View } from '@geti-ui/ui';
import { Delete } from '@geti-ui/ui/icons';
import { clsx } from 'clsx';
import { isEmpty } from 'lodash-es';

import classes from './dataset-view-items-list.module.scss';

export type DatasetView = {
    id: string;
    name: string;
};

type DatasetViewItemProps = {
    datasetView: DatasetView;
    isSelected: boolean;
    action?: ReactNode;
};

const DatasetViewItem = ({ datasetView, isSelected, action }: DatasetViewItemProps) => {
    return (
        <li aria-label={datasetView.name}>
            <View
                padding={'size-200'}
                borderRadius={'regular'}
                UNSAFE_className={clsx(classes.datasetViewInListItem, {
                    [classes.datasetViewListItemSelected]: isSelected,
                })}
            >
                <Flex minWidth={0} alignItems={'center'} justifyContent={'space-between'}>
                    <Heading UNSAFE_className={classes.datasetViewInList}>{datasetView.name}</Heading>
                    {action}
                </Flex>
            </View>
        </li>
    );
};

type DatasetViewItemsListProps = {
    selectedDatasetViewId: string;
    onOpenDeleteConfirmationDialog: (datasetView: DatasetView) => void;
    entireDatasetView: DatasetView;
    otherDatasetViews: DatasetView[];
};

export const DatasetViewItemsList = ({
    selectedDatasetViewId,
    entireDatasetView,
    otherDatasetViews,
    onOpenDeleteConfirmationDialog,
}: DatasetViewItemsListProps) => {
    return (
        <ul className={classes.datasetViewsList} aria-label={'Dataset views list'}>
            <DatasetViewItem
                datasetView={entireDatasetView}
                isSelected={selectedDatasetViewId === entireDatasetView.id}
            />

            {!isEmpty(otherDatasetViews) && <Divider size={'S'} />}

            {otherDatasetViews.map((datasetView) => (
                <DatasetViewItem
                    key={datasetView.id}
                    datasetView={datasetView}
                    isSelected={selectedDatasetViewId === datasetView.id}
                    action={
                        <ActionButton
                            isQuiet
                            aria-label={`Delete ${datasetView.name}`}
                            onPress={() => onOpenDeleteConfirmationDialog(datasetView)}
                        >
                            <Delete />
                        </ActionButton>
                    }
                />
            ))}
        </ul>
    );
};
