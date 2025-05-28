// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';
import { Item, Picker, Text } from '@geti/ui';

interface WorkspacesPickerProps {
    selectedWorkspace: WorkspaceEntity;
    workspaces: WorkspaceEntity[];
    changeWorkspace: (workspace: WorkspaceEntity) => void;
}
export const WorkspacesPicker = ({
    selectedWorkspace,
    workspaces,
    changeWorkspace,
}: WorkspacesPickerProps): JSX.Element => {
    const onSelectionChange = (key: Key) => {
        const newWorkspace = workspaces.find((item) => item.id === key);
        newWorkspace && changeWorkspace(newWorkspace);
    };

    return (
        <Picker
            label={'Workspace'}
            id={`edit-workspace-role-${selectedWorkspace.name}`}
            data-testid={`edit-workspace-role-${selectedWorkspace.name}`}
            width={'50%'}
            items={workspaces}
            selectedKey={selectedWorkspace.id}
            placeholder={'Select workspace'}
            onSelectionChange={onSelectionChange}
        >
            {(item) => (
                <Item key={item.id} textValue={item.name}>
                    <Text id={item.id}>{item.name}</Text>
                </Item>
            )}
        </Picker>
    );
};
