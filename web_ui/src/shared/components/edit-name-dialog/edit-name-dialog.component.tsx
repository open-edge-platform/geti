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
