// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { KeyboardEvent, useEffect, useRef, useState } from 'react';

import { ActionButton, Flex, Loading, TextField, TextFieldRef } from '@geti/ui';
import { Edit } from '@geti/ui/icons';

import { useProjectActions } from '../../../../../core/projects/hooks/use-project-actions.hook';
import { ProjectProps } from '../../../../../core/projects/project.interface';
import { useWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { TruncatedTextWithTooltip } from '../../../../../shared/components/truncated-text/truncated-text.component';
import { ValidationErrorMsg } from '../../../../../shared/components/validation-error-msg/validation-error-msg.component';
import { KeyMap } from '../../../../../shared/keyboard-events/keyboard.interface';
import { isNotCropDomain } from '../../../../../shared/utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import {
    MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME,
    projectNameSchema,
} from '../../../../create-project/components/utils';
import { isYupValidationError } from '../../../../user-management/profile-page/utils';

import classes from './project-name-domain.module.scss';

interface ProjectNameDomainProps {
    classname?: string;
    project: ProjectProps;
    textInRow?: boolean;
    isEditableName?: boolean;
}

export const ProjectNameDomain = ({
    project,
    classname,
    textInRow = false,
    isEditableName = false,
}: ProjectNameDomainProps): JSX.Element => {
    const { name, domains } = project;
    const [editMode, setEditMode] = useState<boolean>(false);
    const [newName, setNewName] = useState<string>(name);
    const [errorMessage, setErrorMessage] = useState<string>('');
    const { editProjectMutation } = useProjectActions();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();

    const nameTextbox = useRef<TextFieldRef>(null);
    const filteredDomains = domains.filter(isNotCropDomain);

    useEffect(() => {
        if (editMode) {
            nameTextbox.current?.focus();
        }
    }, [editMode]);

    const changeName = (inputNewName: string) => {
        setNewName(inputNewName);
        setErrorMessage('');
    };

    const updateName = (value: string) => {
        if (name === value) {
            setEditMode(false);

            return;
        }

        try {
            projectNameSchema().validateSync({ name: value, domain: filteredDomains }, { abortEarly: false });

            errorMessage && setErrorMessage('');

            editProjectMutation.mutate(
                {
                    projectIdentifier: { organizationId, workspaceId, projectId: project.id },
                    project: { ...project, name: newName },
                },
                {
                    onSuccess: () => setEditMode(false),
                }
            );
        } catch (error: unknown) {
            if (isYupValidationError(error)) {
                setErrorMessage(error.message);
            }
            setNewName(name);
        }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
        const updatedName = (e.currentTarget as HTMLInputElement).value;

        if (e.key === KeyMap.Enter) {
            updateName(updatedName);
        }
    };

    const onBlurTextHandler = () => {
        updateName(newName);
    };

    return (
        <Flex direction={'row'} alignItems={'start'} gap={'size-200'} UNSAFE_className={classname}>
            <Flex
                direction={textInRow ? 'row' : 'column'}
                id={`project-name-${idMatchingFormat(name)}`}
                minWidth={0}
                width={'100%'}
            >
                <Flex
                    direction={textInRow || editMode ? 'row' : 'column'}
                    alignItems={textInRow || editMode ? 'center' : 'start'}
                    minWidth={0}
                    width={'100%'}
                >
                    {editMode ? (
                        <>
                            <TextField
                                maxLength={MAX_NUMBER_OF_CHARACTERS_OF_PROJECT_NAME}
                                value={newName}
                                onChange={changeName}
                                onKeyDown={handleKeyDown}
                                onBlur={onBlurTextHandler}
                                ref={nameTextbox}
                                isReadOnly={editProjectMutation.isPending}
                                id={'edit-project-name-field-id'}
                                aria-label={'Edit project name field'}
                            />
                            {editProjectMutation.isPending ? (
                                <Loading mode='inline' marginStart={'size-75'} size={'S'} />
                            ) : (
                                <></>
                            )}
                        </>
                    ) : (
                        <Flex
                            alignItems={'center'}
                            UNSAFE_className={isEditableName ? classes.headerBox : ''}
                            height={'size-400'}
                            minWidth={0}
                            width={'auto'}
                            maxWidth={'100%'}
                        >
                            <TruncatedTextWithTooltip
                                id={'project-name-id'}
                                data-testid={'project-name-id'}
                                UNSAFE_className={[isEditableName ? '' : classes.clickable, classes.projectName].join(
                                    ' '
                                )}
                            >
                                {name}
                            </TruncatedTextWithTooltip>

                            <ActionButton
                                id={'edit-project-name-button-id'}
                                isQuiet
                                onPress={() => setEditMode(!editMode)}
                                UNSAFE_className={classes.editNameButton}
                                aria-label={'Edit name of the project'}
                            >
                                <Edit />
                            </ActionButton>
                        </Flex>
                    )}
                </Flex>

                <ValidationErrorMsg errorMsg={errorMessage} inheritHeight />
            </Flex>
        </Flex>
    );
};
