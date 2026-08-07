// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import {
    AlertDialog,
    Content,
    Dialog,
    DialogContainer,
    DialogTrigger,
    Flex,
    PressableElement,
    Text,
    View,
} from '@geti-ui/ui';
import { ChevronDownSmall } from '@geti-ui/ui/icons';
import { clsx } from 'clsx';
import { isEmpty, partition } from 'lodash-es';

import { DatasetView, DatasetViewItemsList } from './dataset-view-items-list/dataset-view-items-list.component';

import classes from './dataset-view-selector.module.scss';

const ITEMS: DatasetView[] = [
    { id: 'entire-dataset', name: 'Entire dataset' },
    { id: 'collection-one', name: 'Collection one' },
    { id: 'collection-two', name: 'Collection two' },
];

type DeleteDatasetViewDialogProps = {
    datasetView: DatasetView;
    onDelete: () => void;
    onClose: () => void;
};

const DeleteDatasetViewDialog = ({ datasetView, onDelete, onClose }: DeleteDatasetViewDialogProps) => {
    return (
        <AlertDialog
            title={`Delete confirmation`}
            primaryActionLabel={'Delete'}
            onPrimaryAction={onDelete}
            onCancel={onClose}
            secondaryActionLabel={'Close'}
            UNSAFE_className={classes.deleteDatasetView}
        >
            <Content>
                <Text>Are you sure you want to delete the {`"${datasetView.name}"`} dataset view?</Text>
            </Content>
        </AlertDialog>
    );
};

type DatasetViewSelectorProps = {
    selectedDatasetView: DatasetView;
    isDisabled: boolean;
};

const DatasetViewsTrigger = ({ selectedDatasetView, isDisabled }: DatasetViewSelectorProps) => {
    return (
        <PressableElement isDisabled={isDisabled}>
            <div role={'button'} aria-label={'Select dataset view'} aria-disabled={isDisabled} tabIndex={0}>
                <View
                    paddingX={'size-150'}
                    paddingY={'size-50'}
                    borderRadius={'regular'}
                    maxWidth={'size-2400'}
                    UNSAFE_className={clsx(classes.datasetViewsTrigger, {
                        [classes.datasetViewsTriggerDisabled]: isDisabled,
                    })}
                >
                    <Flex alignItems={'center'} gap={'size-200'}>
                        <Text>{selectedDatasetView.name}</Text>

                        <ChevronDownSmall />
                    </Flex>
                </View>
            </div>
        </PressableElement>
    );
};

export const DatasetViewSelector = () => {
    const [isDatasetViewSelectorOpen, setIsDatasetViewSelectorOpen] = useState<boolean>(false);

    const selectedDatasetViewId = ITEMS[0].id;
    const selectedDatasetView = ITEMS.find((item) => item.id === selectedDatasetViewId) ?? ITEMS[0];

    const [datasetViewToBeDeleted, setDatasetViewToBeDeleted] = useState<DatasetView | null>(null);
    const isDeleteDialogOpen = datasetViewToBeDeleted !== null;

    const openDeleteConfirmationDialog = (datasetView: DatasetView) => {
        setIsDatasetViewSelectorOpen(false);
        setDatasetViewToBeDeleted(datasetView);
    };

    const handleDelete = () => {
        setDatasetViewToBeDeleted(null);
    };

    const handleClose = () => {
        setDatasetViewToBeDeleted(null);
    };

    const [[entireDatasetView], otherDatasetViews] = partition(ITEMS, (item) => item.id === 'entire-dataset');
    const onlyEntireDatasetView = isEmpty(otherDatasetViews);

    return (
        <Flex gap={'size-100'} alignItems={'center'}>
            <Text UNSAFE_className={classes.viewsTitle}>Views</Text>

            <DialogTrigger
                hideArrow
                type={'popover'}
                placement={'bottom'}
                isOpen={isDatasetViewSelectorOpen}
                onOpenChange={setIsDatasetViewSelectorOpen}
            >
                <DatasetViewsTrigger selectedDatasetView={selectedDatasetView} isDisabled={onlyEntireDatasetView} />
                <Dialog>
                    <Content>
                        <DatasetViewItemsList
                            entireDatasetView={entireDatasetView}
                            otherDatasetViews={otherDatasetViews}
                            selectedDatasetViewId={selectedDatasetViewId}
                            onOpenDeleteConfirmationDialog={openDeleteConfirmationDialog}
                            onSelectDatasetView={() => {}}
                        />
                    </Content>
                </Dialog>
            </DialogTrigger>

            <DialogContainer onDismiss={handleClose}>
                {isDeleteDialogOpen && (
                    <DeleteDatasetViewDialog
                        datasetView={datasetViewToBeDeleted}
                        onDelete={handleDelete}
                        onClose={handleClose}
                    />
                )}
            </DialogContainer>
        </Flex>
    );
};
