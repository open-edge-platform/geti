// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, FormEvent, useState } from 'react';

import {
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Form,
    Heading,
    Text,
    TextField,
} from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';
import capitalize from 'lodash/capitalize';
import isEmpty from 'lodash/isEmpty';

import { idMatchingFormat } from '../../../test-utils/id-utils';
import { Button } from '../button/button.component';

import classes from './edit-name-dialog.module.scss';

interface EditWorkspaceDialogProps {
    triggerState: OverlayTriggerState;
    onAction: (workspaceName: string) => void;
    defaultName: string;
    names: string[];
    title: string;
    isLoading?: boolean;
    nameLimitations?: Partial<Pick<ComponentProps<typeof TextField>, 'maxLength' | 'minLength'>>;
}

export const EditNameDialog = ({
    title,
    names,
    onAction,
    triggerState,
    defaultName,
    isLoading = false,
    nameLimitations = {},
}: EditWorkspaceDialogProps): JSX.Element => {
    const [updatedName, setUpdatedName] = useState<string>(defaultName);
    const id = idMatchingFormat(title);

    const isEmptyName = isEmpty(updatedName);
    const isDuplicatedName = names.some((name) => name.toLocaleLowerCase() === updatedName.trim().toLocaleLowerCase());
    const isConfirmButtonDisabled = isEmptyName || isDuplicatedName;

    const handleOnChange = (name: string) => {
        setUpdatedName(name);
    };

    const handleConfirm = (event: FormEvent) => {
        event.preventDefault();
        const newName = updatedName.trim();

        if (newName !== defaultName) {
            onAction(newName);
        }

        triggerState.close();
    };

    return (
        <DialogContainer onDismiss={triggerState.close}>
            {triggerState.isOpen && (
                <Dialog size='S' UNSAFE_className={classes.dialog}>
                    <Heading>
                        <Flex alignItems='center' gap='size-100'>
                            <Text>Edit {title}</Text>
                        </Flex>
                    </Heading>
                    <Divider />
                    <Content>
                        <Form onSubmit={handleConfirm}>
                            <TextField
                                id={`edit-${id}-id`}
                                data-testid={`edit-${id}-id`}
                                width={'100%'}
                                value={updatedName}
                                onChange={handleOnChange}
                                label={capitalize(title)}
                                validationState={isDuplicatedName ? 'invalid' : undefined}
                                errorMessage={isDuplicatedName ? `${capitalize(title)} must be unique` : undefined}
                                maxLength={nameLimitations?.maxLength}
                                minLength={nameLimitations?.minLength}
                                // eslint-disable-next-line jsx-a11y/no-autofocus
                                autoFocus
                            />
                            <ButtonGroup align={'end'} marginTop={'size-325'}>
                                <Button variant='secondary' onPress={triggerState.close} id={`cancel-edit-${id}-id`}>
                                    Cancel
                                </Button>
                                <Button
                                    isPending={isLoading}
                                    variant='accent'
                                    isDisabled={isConfirmButtonDisabled}
                                    type='submit'
                                    id={`confirm-edit-${id}-id`}
                                    data-testid={`confirm-edit-${id}-id`}
                                >
                                    Confirm
                                </Button>
                            </ButtonGroup>
                        </Form>
                    </Content>
                </Dialog>
            )}
        </DialogContainer>
    );
};
