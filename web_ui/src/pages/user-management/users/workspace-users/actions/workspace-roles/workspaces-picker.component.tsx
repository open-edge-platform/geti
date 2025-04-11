// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key } from 'react';

import { Item, Picker, Text } from '@adobe/react-spectrum';

import { WorkspaceEntity } from '../../../../../../core/workspaces/services/workspaces.interface';

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
