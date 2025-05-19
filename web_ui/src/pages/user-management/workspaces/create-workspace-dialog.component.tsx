// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useState } from 'react';

import {
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Form,
    Heading,
    TextField,
    View,
} from '@adobe/react-spectrum';
import { Button } from '@geti/ui';

import { useWorkspacesApi } from '../../../core/workspaces/hooks/use-workspaces.hook';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { useWorkspaces } from '../../../providers/workspaces-provider/workspaces-provider.component';
import { MAX_LENGTH_OF_WORKSPACE_NAME, MIN_LENGTH_OF_WORKSPACE_NAME } from './utils';

export const CreateWorkspaceDialog = (): JSX.Element => {
    const [isCreateWorkspaceOpen, setIsCreateWorkspaceOpen] = useState<boolean>(false);
    const [workspaceName, setWorkspaceName] = useState<string>('');
    const { organizationId } = useOrganizationIdentifier();
    const { workspaces } = useWorkspaces();
    const { useCreateWorkspaceMutation } = useWorkspacesApi(organizationId);

    const workspacesNames = workspaces.map((workspace) => workspace.name);
    const createWorkspace = useCreateWorkspaceMutation();

    const isDuplicatedName = workspacesNames.some(
        (name) => name.toLocaleLowerCase() === workspaceName.trim().toLocaleLowerCase()
    );

    const isCreateButtonDisabled = workspaceName === '' || isDuplicatedName;

    const handleOpenCreateWorkspace = (): void => {
        setIsCreateWorkspaceOpen(true);
    };

    const handleCloseCreateWorkspace = (): void => {
        setIsCreateWorkspaceOpen(false);
        setWorkspaceName('');
    };

    const handleOnSubmit = (event: FormEvent): void => {
        event.preventDefault();

        if (isCreateButtonDisabled) {
            return;
        }

        createWorkspace.mutate(
            { name: workspaceName.trim() },
            {
                onSuccess: () => {
                    handleCloseCreateWorkspace();
                },
            }
        );
    };

    return (
        <View>
            <Button variant={'accent'} onPress={handleOpenCreateWorkspace} marginTop={'size-200'}>
                Create new workspace
            </Button>
            <DialogContainer onDismiss={handleCloseCreateWorkspace}>
                {isCreateWorkspaceOpen && (
                    <Dialog>
                        <Heading>Create workspace</Heading>
                        <Divider />
                        <Content>
                            <Form onSubmit={handleOnSubmit}>
                                <TextField
                                    // eslint-disable-next-line jsx-a11y/no-autofocus
                                    autoFocus
                                    minLength={MIN_LENGTH_OF_WORKSPACE_NAME}
                                    maxLength={MAX_LENGTH_OF_WORKSPACE_NAME}
                                    label={'Workspace name'}
                                    value={workspaceName}
                                    onChange={setWorkspaceName}
                                    validationState={isDuplicatedName ? 'invalid' : undefined}
                                    errorMessage={isDuplicatedName ? 'Workspace name must be unique' : undefined}
                                    marginBottom={'size-200'}
                                    aria-label='New workspace new'
                                />

                                <Divider size={'S'} marginY={'size-200'} />

                                <ButtonGroup align={'end'}>
                                    <Button variant={'secondary'} onPress={handleCloseCreateWorkspace}>
                                        Cancel
                                    </Button>
                                    <Button
                                        type={'submit'}
                                        isPending={createWorkspace.isPending}
                                        variant={'accent'}
                                        isDisabled={isCreateButtonDisabled}
                                    >
                                        Create
                                    </Button>
                                </ButtonGroup>
                            </Form>
                        </Content>
                    </Dialog>
                )}
            </DialogContainer>
        </View>
    );
};
