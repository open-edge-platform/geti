// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Form, Heading, TextField } from '@geti-ui/ui';
import { isEmpty } from 'lodash-es';

import { SelectedMediaCount } from '../selected-media-count/selected-media-count.component';

type SaveDatasetViewDialogProps = {
    onClose: () => void;
    selectedMediaCount: number;
};

const SaveDatasetViewDialog = ({ onClose, selectedMediaCount }: SaveDatasetViewDialogProps) => {
    const [viewName, setViewName] = useState<string>('');

    const isSaveDisabled = isEmpty(viewName);

    const saveView = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onClose();
    };

    return (
        <Dialog>
            <Heading>Save view</Heading>
            <Divider size={'S'} />
            <Content>
                <SelectedMediaCount count={selectedMediaCount} />
                <Form id={'view-name-form'} onSubmit={saveView} marginTop={'size-200'}>
                    <TextField label={'View name'} value={viewName} onChange={setViewName} />
                </Form>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose}>
                    Close
                </Button>
                <Button variant={'accent'} type={'submit'} form={'view-name-form'} isDisabled={isSaveDisabled}>
                    Save
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};

type SaveDatasetViewProps = {
    selectedMediaCount: number;
};

export const SaveDatasetView = ({ selectedMediaCount }: SaveDatasetViewProps) => {
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
                    <SaveDatasetViewDialog onClose={closeDialog} selectedMediaCount={selectedMediaCount} />
                )}
            </DialogContainer>
        </>
    );
};
