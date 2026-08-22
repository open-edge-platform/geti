// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useMemo, useState } from 'react';

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
import { ENTIRE_DATASET_VIEW_ID, useDatasetViewId } from 'hooks/use-dataset-view-id.hook';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { DatasetView, DatasetViewItemsList } from './dataset-view-items-list/dataset-view-items-list.component';
import { RenameDatasetView } from './rename-dataset-view.component';

import classes from './dataset-view-selector.module.scss';

type DeleteDatasetViewDialogProps = {
    datasetView: DatasetView;
    onDelete: () => void;
    onClose: () => void;
};

const DeleteDatasetViewDialog = ({ datasetView, onDelete, onClose }: DeleteDatasetViewDialogProps) => {
    const { t } = useTranslation();

    return (
        <AlertDialog
            title={t('dataset.viewDeleteConfirmTitle')}
            primaryActionLabel={t('common.delete')}
            onPrimaryAction={onDelete}
            onCancel={onClose}
            secondaryActionLabel={t('dataset.closeButton')}
        >
            <Content>
                <Text>{t('dataset.viewDeleteConfirmText', { name: datasetView.name })}</Text>
            </Content>
        </AlertDialog>
    );
};

type DatasetViewsTriggerProps = {
    selectedDatasetView: DatasetView;
    isDisabled: boolean;
};

const DatasetViewsTrigger = ({ selectedDatasetView, isDisabled }: DatasetViewsTriggerProps) => {
    const { t } = useTranslation();

    return (
        <PressableElement isDisabled={isDisabled}>
            <div
                role={'button'}
                aria-label={t('dataset.selectViewAriaLabel')}
                aria-disabled={isDisabled}
                tabIndex={isDisabled ? -1 : 0}
            >
                <View
                    paddingX={'size-150'}
                    paddingY={'size-100'}
                    borderRadius={'regular'}
                    maxWidth={'size-2400'}
                    UNSAFE_className={clsx(classes.datasetViewsTrigger, {
                        [classes.datasetViewsTriggerDisabled]: isDisabled,
                    })}
                >
                    <Flex alignItems={'center'} gap={'size-200'}>
                        <Text UNSAFE_className={classes.datasetViewName}>{selectedDatasetView.name}</Text>

                        <ChevronDownSmall />
                    </Flex>
                </View>
            </div>
        </PressableElement>
    );
};

type DatasetViewSelectorProps = {
    datasetViews: DatasetView[];
};

export const DatasetViewSelector = ({ datasetViews }: DatasetViewSelectorProps) => {
    const { t } = useTranslation();
    const [isDatasetViewSelectorOpen, setIsDatasetViewSelectorOpen] = useState<boolean>(false);

    const entireDataset = useMemo(() => {
        return { id: ENTIRE_DATASET_VIEW_ID, name: t('dataset.entireDataset') };
    }, [t]);

    const datasetViewsWithDefaultView = useMemo(() => {
        return [entireDataset, ...datasetViews];
    }, [entireDataset, datasetViews]);

    const [datasetViewId, setDatasetViewId] = useDatasetViewId();
    const selectedDatasetView = datasetViewsWithDefaultView.find((item) => item.id === datasetViewId) ?? entireDataset;

    const [datasetViewToBeDeleted, setDatasetViewToBeDeleted] = useState<DatasetView | null>(null);
    const [datasetViewToBeRenamed, setDatasetViewToBeRenamed] = useState<DatasetView | null>(null);

    const openDeleteConfirmationDialog = (datasetView: DatasetView) => {
        setIsDatasetViewSelectorOpen(false);
        setDatasetViewToBeDeleted(datasetView);
    };

    const openRenameDialog = (datasetView: DatasetView) => {
        setIsDatasetViewSelectorOpen(false);
        setDatasetViewToBeRenamed(datasetView);
    };

    const handleDelete = () => {
        setDatasetViewToBeDeleted(null);
    };

    const handleCloseDeleteDialog = () => {
        setDatasetViewToBeDeleted(null);
    };

    const handleCloseRenameDialog = () => {
        setDatasetViewToBeRenamed(null);
    };

    const onlyEntireDatasetView = isEmpty(datasetViews);

    // When the datasetViewId is invalid, i.e. not found in the datasetViews array, set it to the default view id.
    // TODO: Once backend is ready, check if we can remove `useEffect`.
    useEffect(() => {
        if (!datasetViewsWithDefaultView.some(({ id }) => id === datasetViewId)) {
            setDatasetViewId(ENTIRE_DATASET_VIEW_ID);
        }
    }, [datasetViewId, datasetViewsWithDefaultView, setDatasetViewId]);

    const onSelectDatasetView = (id: string) => {
        setDatasetViewId(id);
        setIsDatasetViewSelectorOpen(false);
    };

    return (
        <Flex gap={'size-100'} alignItems={'center'}>
            <Text UNSAFE_className={classes.viewsTitle}>{t('dataset.viewsTitle')}</Text>

            <DialogTrigger
                hideArrow
                type={'popover'}
                placement={'bottom left'}
                isOpen={isDatasetViewSelectorOpen}
                onOpenChange={setIsDatasetViewSelectorOpen}
            >
                <DatasetViewsTrigger selectedDatasetView={selectedDatasetView} isDisabled={onlyEntireDatasetView} />
                <Dialog>
                    <Content>
                        <DatasetViewItemsList
                            entireDatasetView={entireDataset}
                            otherDatasetViews={datasetViews}
                            selectedDatasetViewId={datasetViewId}
                            onOpenDeleteConfirmationDialog={openDeleteConfirmationDialog}
                            onSelectDatasetView={onSelectDatasetView}
                            onOpenRenameDialog={openRenameDialog}
                        />
                    </Content>
                </Dialog>
            </DialogTrigger>

            <DialogContainer onDismiss={handleCloseDeleteDialog}>
                {datasetViewToBeDeleted !== null && (
                    <DeleteDatasetViewDialog
                        datasetView={datasetViewToBeDeleted}
                        onDelete={handleDelete}
                        onClose={handleCloseDeleteDialog}
                    />
                )}
            </DialogContainer>
            <DialogContainer onDismiss={handleCloseRenameDialog}>
                {datasetViewToBeRenamed && (
                    <RenameDatasetView datasetView={datasetViewToBeRenamed} onClose={handleCloseRenameDialog} />
                )}
            </DialogContainer>
        </Flex>
    );
};
