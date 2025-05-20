// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useRef, useState } from 'react';

import {
    Button,
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
    TextFieldRef,
} from '@geti/ui';

import { Info } from '../../../../assets/icons';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE, USER_ROLE } from '../../../../core/users/users.interface';
import { WorkspaceIdentifier } from '../../../../core/workspaces/services/workspaces.interface';
import { useIsSaasEnv } from '../../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { isYupValidationError } from '../../profile-page/utils';
import { ErrorMessage } from '../add-member-popup/error-message/error-message.component';
import { RolePicker } from '../old-project-users/role-picker.component';
import { MAX_NUMBER_OF_CHARACTERS, validateEmail, validateUserEmail } from '../utils';

interface InviteUserProps extends WorkspaceIdentifier {
    id: string;
    isAdmin: boolean;
}
export const InviteUser = ({ isAdmin, id, organizationId, workspaceId }: InviteUserProps): JSX.Element => {
    const roles = isAdmin
        ? [USER_ROLE.WORKSPACE_CONTRIBUTOR, USER_ROLE.WORKSPACE_ADMIN]
        : [USER_ROLE.WORKSPACE_CONTRIBUTOR];
    const [selectedRole, setSelectedRole] = useState<USER_ROLE>(roles[0]);

    const [isOpen, setIsOpen] = useState<boolean>(false);
    const [email, setEmail] = useState<string>('');
    const [errorMsg, setErrorMsg] = useState<string>('');

    const { useGetUsersQuery, useInviteUserMutation } = useUsers();
    const { users } = useGetUsersQuery(organizationId);
    const inviteUser = useInviteUserMutation(organizationId);

    const inputRef = useRef<TextFieldRef>(null);

    const isValidEmail = validateEmail.isValidSync(email);
    const isBtnDisabled = !isValidEmail || !email || !!errorMsg;

    const handleOpen = (): void => {
        setIsOpen(true);
    };

    const handleChange = (value: string): void => {
        try {
            setEmail(value);

            validateUserEmail(value, users ?? []).validateSync({ email: value }, { abortEarly: false });

            errorMsg && setErrorMsg('');
        } catch (error: unknown) {
            if (isYupValidationError(error)) {
                error.inner.length && setErrorMsg(error.inner[0].message);
            }
        }
    };

    const handleDismiss = (): void => {
        setIsOpen(false);

        email && setEmail('');
        errorMsg && setErrorMsg('');
    };

    const isSaasEnvironment = useIsSaasEnv();

    const handleSubmit = (event: FormEvent): void => {
        event.preventDefault();

        inviteUser.mutate(
            {
                organizationId,
                email: email.trim(),
                roles: [
                    {
                        resourceId: workspaceId,
                        resourceType: RESOURCE_TYPE.WORKSPACE,
                        role: selectedRole,
                    },
                    {
                        resourceId: organizationId,
                        resourceType: RESOURCE_TYPE.ORGANIZATION,
                        role:
                            !isSaasEnvironment && selectedRole === USER_ROLE.WORKSPACE_ADMIN
                                ? USER_ROLE.ORGANIZATION_ADMIN
                                : USER_ROLE.ORGANIZATION_CONTRIBUTOR,
                    },
                ],
            },
            {
                onSuccess: handleDismiss,
            }
        );
    };

    return (
        <>
            <Button variant={'accent'} onPress={handleOpen} id={id}>
                Send invite
            </Button>
            <DialogContainer onDismiss={handleDismiss}>
                {isOpen && (
                    <Dialog>
                        <Heading>Send invite</Heading>
                        <Divider size={'S'} />
                        <Content UNSAFE_style={{ overflow: 'hidden' }}>
                            <Form onSubmit={handleSubmit}>
                                <TextField
                                    ref={inputRef}
                                    // eslint-disable-next-line jsx-a11y/no-autofocus
                                    autoFocus
                                    id={'email-address-id'}
                                    type={'email'}
                                    label={'Email address'}
                                    autoComplete={'email'}
                                    value={email}
                                    onChange={handleChange}
                                    maxLength={MAX_NUMBER_OF_CHARACTERS}
                                    validationState={!isValidEmail || errorMsg ? 'invalid' : undefined}
                                />
                                <RolePicker
                                    roles={roles}
                                    selectedRole={selectedRole}
                                    setSelectedRole={setSelectedRole}
                                />
                                <ErrorMessage marginTop={'size-150'} message={errorMsg} id={'invite'} />
                                <Flex alignItems={'center'} gap={'size-100'} marginTop={'size-150'}>
                                    <Info />
                                    <Text>Note: Invitation is only valid for 7 days.</Text>
                                </Flex>
                                <ButtonGroup align={'end'} marginTop={'size-350'}>
                                    <Button variant={'secondary'} onPress={handleDismiss} id={'cancel-btn-id'}>
                                        Cancel
                                    </Button>
                                    <Button
                                        isPending={inviteUser.isPending}
                                        isDisabled={isBtnDisabled}
                                        id={'send-btn-id'}
                                        type={'submit'}
                                        aria-label={'send invitation'}
                                    >
                                        Send
                                    </Button>
                                </ButtonGroup>
                            </Form>
                        </Content>
                    </Dialog>
                )}
            </DialogContainer>
        </>
    );
};
