// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, Divider, Form, Heading, TextField } from '@geti-ui/ui';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { useRenameDatasetViewMutation } from './api/use-rename-dataset-view-mutation';
import { DatasetView } from './type';

type RenameDatasetViewProps = {
    datasetView: DatasetView;
    datasetViews: DatasetView[];
    onClose: () => void;
};

export const RenameDatasetView = ({ datasetView, onClose, datasetViews }: RenameDatasetViewProps) => {
    const projectId = useProjectIdentifier();
    const [newName, setNewName] = useState(datasetView.name);
    const { t } = useTranslation();
    const renameDatasetViewMutation = useRenameDatasetViewMutation();

    const isDuplicateName = datasetViews.some((view) => view.name === newName.trim());
    const isSaveDisabled = newName === datasetView.name || isEmpty(newName.trim()) || isDuplicateName;

    const rename = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        renameDatasetViewMutation.mutate(
            {
                params: {
                    path: {
                        project_id: projectId,
                        dataset_view_id: datasetView.id,
                    },
                },
                body: {
                    name: newName.trim(),
                },
            },
            {
                onSuccess: onClose,
            }
        );
    };

    return (
        <Dialog>
            <Heading>{t('dataset.renameViewHeading')}</Heading>
            <Divider />
            <Content>
                <Form id={'rename-dataset-view-name'} onSubmit={rename}>
                    <TextField
                        // eslint-disable-next-line jsx-a11y/no-autofocus
                        autoFocus
                        value={newName}
                        onChange={setNewName}
                        label={t('dataset.viewNameLabel')}
                        validationState={isDuplicateName ? 'invalid' : undefined}
                        errorMessage={isDuplicateName ? t('dataset.renameDuplicateError') : undefined}
                    />
                </Form>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose}>
                    {t('common.cancel')}
                </Button>
                <Button
                    type={'submit'}
                    form={'rename-dataset-view-name'}
                    isDisabled={isSaveDisabled}
                    isPending={renameDatasetViewMutation.isPending}
                >
                    {t('common.save')}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
