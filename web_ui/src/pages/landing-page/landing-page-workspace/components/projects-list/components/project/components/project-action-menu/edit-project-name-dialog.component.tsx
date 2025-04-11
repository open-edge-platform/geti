// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FormEvent, useState } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Form, Heading } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { useProjectActions } from '../../../../../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../../../../../core/projects/project.interface';
import { useWorkspaceIdentifier } from '../../../../../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { Button } from '../../../../../../../../../shared/components/button/button.component';
import { LimitedTextField } from '../../../../../../../../../shared/components/limited-text-field/limited-text-field.component';

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
                            <LimitedTextField
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
