// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

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
    Form,
    Heading,
    Item,
    Picker,
} from '@geti-ui/ui';
import { isEmpty } from 'lodash-es';

import { SelectedMediaCount } from '../selected-media-count/selected-media-count.component';

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

    const assignMedia = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onClose();
    };

    return (
        <Dialog>
            <Heading>Assign to existing view</Heading>
            <Divider size={'S'} />
            <Content>
                <SelectedMediaCount count={selectedMediaIds.length} />
                <Form id={'assign-to-existing-view-form'} onSubmit={assignMedia} marginTop={'size-200'}>
                    <Picker
                        items={datasetViews}
                        label={'Assign to'}
                        placeholder={'Select a view'}
                        selectedKey={selectedDatasetViewId}
                        onSelectionChange={(viewId) => setSelectedDatasetViewId(viewId?.toString() ?? null)}
                    >
                        {(item) => <Item key={item.id}>{item.name}</Item>}
                    </Picker>
                </Form>
            </Content>
            <ButtonGroup>
                <Button onPress={onClose} variant={'secondary'}>
                    Close
                </Button>
                <Button type={'submit'} form={'assign-to-existing-view-form'} variant={'accent'}>
                    Assign
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
                Assign to existing view
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
