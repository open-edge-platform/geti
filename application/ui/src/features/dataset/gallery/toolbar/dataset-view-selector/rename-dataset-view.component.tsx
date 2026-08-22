// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, Divider, Form, Heading, TextField } from '@geti-ui/ui';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { DatasetView } from './dataset-view-items-list/dataset-view-items-list.component';

type RenameDatasetViewProps = {
    datasetView: DatasetView;
    onClose: () => void;
};

export const RenameDatasetView = ({ datasetView, onClose }: RenameDatasetViewProps) => {
    const [newName, setNewName] = useState(datasetView.name);
    const { t } = useTranslation();
    const isSaveDisabled = newName === datasetView.name || isEmpty(newName.trim());

    const rename = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onClose();
    };

    return (
        <Dialog>
            <Heading>{t('dataset.renameViewHeading')}</Heading>
            <Divider />
            <Content>
                <Form id={'rename-dataset-view-name'} onSubmit={rename}>
                    {/* eslint-disable-next-line jsx-a11y/no-autofocus */}
                    <TextField autoFocus value={newName} onChange={setNewName} label={t('dataset.viewNameLabel')} />
                </Form>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose}>
                    {t('common.cancel')}
                </Button>
                <Button type={'submit'} form={'rename-dataset-view-name'} isDisabled={isSaveDisabled}>
                    {t('common.save')}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
