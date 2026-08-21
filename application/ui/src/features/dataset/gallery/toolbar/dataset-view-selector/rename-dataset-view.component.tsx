// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, Divider, Form, Heading, TextField } from '@geti-ui/ui';
import { isEmpty } from 'lodash-es';

import { DatasetView } from './dataset-view-items-list/dataset-view-items-list.component';

type RenameDatasetViewProps = {
    datasetView: DatasetView;
    onClose: () => void;
};

export const RenameDatasetView = ({ datasetView, onClose }: RenameDatasetViewProps) => {
    const [newName, setNewName] = useState(datasetView.name);
    const isEditDisabled = newName === datasetView.name || isEmpty(newName.trim());

    const edit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onClose();
    };

    return (
        <Dialog>
            <Heading>Edit dataset view</Heading>
            <Divider />
            <Content>
                <Form id={'edit-dataset-view-name'} onSubmit={edit}>
                    {/* eslint-disable-next-line jsx-a11y/no-autofocus */}
                    <TextField autoFocus value={newName} onChange={setNewName} label={'View name'} />
                </Form>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose}>
                    Cancel
                </Button>
                <Button type={'submit'} form={'edit-dataset-view-name'} isDisabled={isEditDisabled}>
                    Edit
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
