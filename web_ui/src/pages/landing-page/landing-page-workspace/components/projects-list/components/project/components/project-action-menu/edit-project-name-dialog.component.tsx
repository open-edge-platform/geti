// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Form, Heading, TextField } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { useProjectActions } from '../../../../../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../../../../../core/projects/project.interface';
import { useWorkspaceIdentifier } from '../../../../../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME } from '../../../../../../../../create-project/components/utils';

interface EditProjectNameDialogProps {
    onClose: () => void;
    isOpen: boolean;
    project: ProjectProps;
}

const useEditProjectName = () => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { editProjectMutation } = useProjectActions();

    const editProjectName = async (newProject: ProjectProps, onSuccess: () => void) => {
        editProjectMutation.mutate(
            {
                project: newProject,
                projectIdentifier: { projectId: newProject.id, workspaceId, organizationId },
            },
            {
                onSuccess: () => {
                    onSuccess();
                },
            }
        );
    };

    return { editProjectName, isLoading: editProjectMutation.isPending };
};

export const EditProjectNameDialog = ({ onClose, isOpen, project }: EditProjectNameDialogProps): JSX.Element => {
    const [newProjectName, setNewProjectName] = useState(project.name);
    const { editProjectName, isLoading } = useEditProjectName();
    const isSaveButtonDisabled = isEmpty(newProjectName) || newProjectName === project.name || isLoading;

    const handleEditProjectName = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        if (isSaveButtonDisabled) {
            return;
        }

        await editProjectName({ ...project, name: newProjectName }, onClose);
    };

    const handleDismiss = () => {
        onClose();
        setNewProjectName(project.name);
    };

    return (
        <DialogContainer onDismiss={handleDismiss}>
            {isOpen && (
                <Dialog>
                    <Heading>Edit project name</Heading>
                    <Divider />
                    <Content>
                        <Form onSubmit={handleEditProjectName}>
                            <TextField
                                maxLength={MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME}
                                //eslint-disable-next-line jsx-a11y/no-autofocus
                                autoFocus
                                value={newProjectName}
                                onChange={setNewProjectName}
                                width='100%'
                                id={'edit-project-name-field-id'}
                                aria-label={'Edit project name field'}
                                isReadOnly={isLoading}
                            />
                            <ButtonGroup align={'end'} marginTop={'size-350'}>
                                <Button variant='secondary' onPress={handleDismiss}>
                                    Cancel
                                </Button>
                                <Button
                                    type='submit'
                                    variant='accent'
                                    isDisabled={isSaveButtonDisabled}
                                    isPending={isLoading}
                                >
                                    Save
                                </Button>
                            </ButtonGroup>
                        </Form>
                    </Content>
                </Dialog>
            )}
        </DialogContainer>
    );
};
