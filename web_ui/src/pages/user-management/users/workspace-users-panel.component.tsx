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

import { Key, useEffect } from 'react';

import { Flex, Item, Picker, Text } from '@adobe/react-spectrum';

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { hasEqualId } from '../../../shared/utils';
import { idMatchingFormat } from '../../../test-utils/id-utils';

const ALL_WORKSPACES = {
    id: '',
    text: 'All workspaces',
};

interface WorkspaceUsersPanelProps {
    selectedWorkspace: string | undefined;
    setSelectedWorkspace: (key: string | undefined) => void;
}

export const WorkspaceUsersPanel = ({
    selectedWorkspace,
    setSelectedWorkspace,
}: WorkspaceUsersPanelProps): JSX.Element => {
    const { workspaces } = useWorkspaces();
    const { FEATURE_FLAG_WORKSPACE_ACTIONS } = useFeatureFlags();
    const items = [ALL_WORKSPACES, ...workspaces.map(({ id, name }) => ({ id, text: name }))];

    const onSelectionChange = (key: Key) => {
        const newSelectedWorkspace = workspaces.find(hasEqualId(key.toString()));
        setSelectedWorkspace(newSelectedWorkspace?.id ?? ALL_WORKSPACES.id);
    };

    const workspaceCreateDisabled = workspaces.length === 1 && !FEATURE_FLAG_WORKSPACE_ACTIONS;

    useEffect(() => {
        //Note: First workspace is selected by default if we have don't have option to create new one
        if (workspaceCreateDisabled && !selectedWorkspace) {
            setSelectedWorkspace(workspaces[0].id);
        }
    }, [workspaceCreateDisabled, setSelectedWorkspace, workspaces, selectedWorkspace]);

    return (
        <Flex direction={'column'}>
            <Picker
                placeholder={'All workspaces'}
                id={'select-workspace-users-list-id'}
                data-testid={'select-workspace-users-list-id'}
                aria-label='Select workspace'
                items={items}
                selectedKey={selectedWorkspace}
                isDisabled={workspaceCreateDisabled}
                isQuiet={workspaceCreateDisabled}
                onSelectionChange={onSelectionChange}
            >
                {(item) => (
                    <Item key={item.id} textValue={item.text}>
                        <Text id={`${item.id}-${idMatchingFormat(item.text)}-id`}>{item.text}</Text>
                    </Item>
                )}
            </Picker>
        </Flex>
    );
};
