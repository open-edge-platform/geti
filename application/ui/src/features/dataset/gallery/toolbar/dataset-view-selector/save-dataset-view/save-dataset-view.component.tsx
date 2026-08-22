// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Form, Heading, TextField } from '@geti-ui/ui';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { SelectedMediaCount } from '../selected-media-count/selected-media-count.component';

type SaveDatasetViewDialogProps = {
    onClose: () => void;
    selectedMediaIds: string[];
};

const SaveDatasetViewDialog = ({ onClose, selectedMediaIds }: SaveDatasetViewDialogProps) => {
    const [viewName, setViewName] = useState<string>('');
    const { t } = useTranslation();

    const isSaveDisabled = isEmpty(viewName.trim());

    const saveView = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onClose();
    };

    return (
        <Dialog>
            <Heading>{t('dataset.saveViewHeading')}</Heading>
            <Divider size={'S'} />
            <Content>
                <SelectedMediaCount count={selectedMediaIds.length} />
                <Form id={'view-name-form'} onSubmit={saveView} marginTop={'size-200'}>
                    {/* eslint-disable-next-line jsx-a11y/no-autofocus */}
                    <TextField autoFocus label={t('dataset.viewNameLabel')} value={viewName} onChange={setViewName} />
                </Form>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose}>
                    {t('dataset.closeButton')}
                </Button>
                <Button variant={'accent'} type={'submit'} form={'view-name-form'} isDisabled={isSaveDisabled}>
                    {t('common.save')}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};

type SaveDatasetViewProps = {
    selectedMediaIds: string[];
};

export const SaveDatasetView = ({ selectedMediaIds }: SaveDatasetViewProps) => {
    const [isSaveViewDialogOpen, setIsSaveViewDialogOpen] = useState<boolean>(false);

    const closeDialog = () => {
        setIsSaveViewDialogOpen(false);
    };

    return (
        <>
            <Button variant={'primary'} onPress={() => setIsSaveViewDialogOpen(true)}>
                Save view
            </Button>
            <DialogContainer onDismiss={closeDialog}>
                {isSaveViewDialogOpen && (
                    <SaveDatasetViewDialog onClose={closeDialog} selectedMediaIds={selectedMediaIds} />
                )}
            </DialogContainer>
        </>
    );
};
