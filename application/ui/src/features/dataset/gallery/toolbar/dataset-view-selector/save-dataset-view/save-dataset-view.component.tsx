// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Form, Heading, TextField } from '@geti-ui/ui';
import { ENTIRE_DATASET_VIEW_ID, useDatasetViewId } from 'hooks/use-dataset-view-id.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { useCreateDatasetViewMutation } from '../api/use-create-dataset-view';
import { SelectedMediaCount } from '../selected-media-count/selected-media-count.component';
import { DatasetView } from '../type';

type SaveDatasetViewDialogProps = {
    onClose: () => void;
    selectedMediaIds: string[];
    datasetViews: DatasetView[];
};

const SaveDatasetViewDialog = ({ onClose, selectedMediaIds, datasetViews }: SaveDatasetViewDialogProps) => {
    const [viewName, setViewName] = useState<string>('');
    const { t } = useTranslation();
    const projectId = useProjectIdentifier();
    const createDatasetViewMutation = useCreateDatasetViewMutation();
    const isDuplicatedName = datasetViews.some((view) => view.name === viewName.trim());

    const isSaveDisabled = isEmpty(viewName.trim()) || isDuplicatedName;

    const saveView = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        createDatasetViewMutation.mutate(
            {
                params: {
                    path: {
                        project_id: projectId,
                    },
                },
                body: {
                    name: viewName.trim(),
                    media_ids: selectedMediaIds,
                },
            },
            {
                onSuccess: onClose,
            }
        );
    };

    return (
        <Dialog>
            <Heading>{t('dataset.saveViewHeading')}</Heading>
            <Divider size={'S'} />
            <Content>
                <SelectedMediaCount count={selectedMediaIds.length} />
                <Form id={'view-name-form'} onSubmit={saveView} marginTop={'size-200'}>
                    <TextField
                        // eslint-disable-next-line jsx-a11y/no-autofocus
                        autoFocus
                        label={t('dataset.viewNameLabel')}
                        value={viewName}
                        onChange={setViewName}
                        validationState={isDuplicatedName ? 'invalid' : undefined}
                        errorMessage={isDuplicatedName ? t('dataset.saveDuplicateError') : undefined}
                    />
                </Form>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose}>
                    {t('dataset.closeButton')}
                </Button>
                <Button
                    variant={'accent'}
                    type={'submit'}
                    form={'view-name-form'}
                    isDisabled={isSaveDisabled}
                    isPending={createDatasetViewMutation.isPending}
                >
                    {t('common.save')}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};

type SaveDatasetViewProps = {
    selectedMediaIds: string[];
    datasetViews: DatasetView[];
};

export const SaveDatasetView = ({ selectedMediaIds, datasetViews }: SaveDatasetViewProps) => {
    const { t } = useTranslation();
    const [datasetViewId] = useDatasetViewId();

    const [isSaveViewDialogOpen, setIsSaveViewDialogOpen] = useState<boolean>(false);

    const closeDialog = () => {
        setIsSaveViewDialogOpen(false);
    };

    if (datasetViewId !== ENTIRE_DATASET_VIEW_ID) {
        return null;
    }

    return (
        <>
            <Button variant={'primary'} onPress={() => setIsSaveViewDialogOpen(true)}>
                {t('dataset.saveViewButton')}
            </Button>
            <DialogContainer onDismiss={closeDialog}>
                {isSaveViewDialogOpen && (
                    <SaveDatasetViewDialog
                        onClose={closeDialog}
                        selectedMediaIds={selectedMediaIds}
                        datasetViews={datasetViews}
                    />
                )}
            </DialogContainer>
        </>
    );
};
