// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Form,
    Heading,
    Item,
    Picker,
    Text,
} from '@geti-ui/ui';
import { Info } from '@geti-ui/ui/icons';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { SelectedMediaCount } from '../selected-media-count/selected-media-count.component';

import classes from './assign-to-existing-view.module.scss';

type DatasetView = {
    id: string;
    name: string;
};

type AssignToExistingViewDialogProps = {
    datasetViews: DatasetView[];
    onClose: () => void;
    selectedMediaIds: string[];
};

const AssignToExistingViewDialog = ({ datasetViews, selectedMediaIds, onClose }: AssignToExistingViewDialogProps) => {
    const [selectedDatasetViewId, setSelectedDatasetViewId] = useState<string | null>(null);
    const { t } = useTranslation();

    const assignMedia = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onClose();
    };

    return (
        <Dialog>
            <Heading>{t('dataset.assignToExistingViewHeading')}</Heading>
            <Divider size={'S'} />
            <Content>
                <SelectedMediaCount count={selectedMediaIds.length} />
                <Form id={'assign-to-existing-view-form'} onSubmit={assignMedia} marginTop={'size-200'}>
                    <Picker
                        items={datasetViews}
                        label={t('dataset.assignToLabel')}
                        placeholder={t('dataset.selectViewPlaceholder')}
                        selectedKey={selectedDatasetViewId}
                        onSelectionChange={(viewId) => setSelectedDatasetViewId(viewId?.toString() ?? null)}
                    >
                        {(item) => <Item key={item.id}>{item.name}</Item>}
                    </Picker>
                </Form>
                <Flex gap={'size-50'} marginTop={'size-250'}>
                    <Info />
                    <Text UNSAFE_className={classes.note}>{t('dataset.assignNote')}</Text>
                </Flex>
            </Content>
            <ButtonGroup>
                <Button onPress={onClose} variant={'secondary'}>
                    {t('dataset.closeButton')}
                </Button>
                <Button type={'submit'} form={'assign-to-existing-view-form'} variant={'accent'}>
                    {t('dataset.assignButton')}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};

type AssignToExistingViewProps = {
    datasetViews: DatasetView[];
    selectedMediaIds: string[];
};

export const AssignToExistingView = ({ datasetViews, selectedMediaIds }: AssignToExistingViewProps) => {
    const { t } = useTranslation();
    const [isAssignToExistingViewOpen, setIsAssignToExistingViewOpen] = useState<boolean>(false);
    const isAssignToExistingViewDisabled = isEmpty(datasetViews);

    const closeDialog = () => {
        setIsAssignToExistingViewOpen(false);
    };

    return (
        <>
            <Button
                variant={'primary'}
                onPress={() => setIsAssignToExistingViewOpen(true)}
                isDisabled={isAssignToExistingViewDisabled}
            >
                {t('dataset.assignToExistingViewButton')}
            </Button>
            <DialogContainer onDismiss={closeDialog}>
                {isAssignToExistingViewOpen && (
                    <AssignToExistingViewDialog
                        datasetViews={datasetViews}
                        onClose={closeDialog}
                        selectedMediaIds={selectedMediaIds}
                    />
                )}
            </DialogContainer>
        </>
    );
};
