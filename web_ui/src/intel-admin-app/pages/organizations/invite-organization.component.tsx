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
} from '@adobe/react-spectrum';
import { Button } from '@shared/components/button/button.component';
import { useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import {
    ORGANIZATIONS_QUERY_LIMIT,
    useOrganizationsApi,
} from '../../../core/organizations/hook/use-organizations-api.hook';
import { GetOrganizationsQueryOptions } from '../../../core/organizations/services/organizations-service.interface';
import QUERY_KEYS from '../../../core/requests/query-keys';
import { ErrorMessage } from '../../../pages/user-management/users/add-member-popup/error-message/error-message.component';
import { validateEmail } from '../../../pages/user-management/users/utils';

const MIN_ORG_NAME = 1;
const MAX_ORG_NAME = 50;

interface InviteOrganizationProps {
    organizationsQueryOptions: GetOrganizationsQueryOptions;
}
export const InviteOrganization = ({ organizationsQueryOptions }: InviteOrganizationProps): JSX.Element => {
    const [isSendInviteOpen, setIsSendInviteOpen] = useState<boolean>(false);
    const [email, setEmail] = useState<string>('');
    const [organizationName, setOrganizationName] = useState<string>('');
    const [error, setError] = useState<string>('');

    const { useInviteOrganizationMutation } = useOrganizationsApi();
    const inviteOrganization = useInviteOrganizationMutation();

    const isValidEmail = validateEmail.isValidSync(email);
    const isSendInviteDisabled = email === '' || organizationName === '' || !isValidEmail;

    const queryClient = useQueryClient();
    const handleOpenSendInvite = (): void => {
        setIsSendInviteOpen(true);
    };

    const handleCloseSendInvite = (): void => {
        setEmail('');
        setError('');
        setOrganizationName('');
        setIsSendInviteOpen(false);
    };

    const handleOnSubmit = async (event: FormEvent): Promise<void> => {
        event.preventDefault();

        setError('');

        if (isSendInviteDisabled) {
            return;
        }

        inviteOrganization.mutate(
            {
                organizationName,
                adminEmail: email,
            },
            {
                onSuccess: async () => {
                    const queryOptions = {
                        ...organizationsQueryOptions,
                        limit: ORGANIZATIONS_QUERY_LIMIT,
                    };

                    handleCloseSendInvite();

                    await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ORGANIZATIONS(queryOptions) });
                },
                onError: (invitationError: AxiosError) => {
                    setError(invitationError.message);
                },
            }
        );
    };

    return (
        <>
            <Button variant={'accent'} onPress={handleOpenSendInvite} id={'send-organization-invitation'}>
                Send invite
            </Button>
            <DialogContainer onDismiss={handleCloseSendInvite}>
                {isSendInviteOpen && (
                    <Dialog>
                        <Heading>Send invite</Heading>
                        <Divider />
                        <Content>
                            <Form onSubmit={handleOnSubmit}>
                                <TextField
                                    // eslint-disable-next-line jsx-a11y/no-autofocus
                                    autoFocus
                                    label={'Email address'}
                                    value={email}
                                    aria-label={'Email address'}
                                    onChange={setEmail}
                                    validationState={isValidEmail ? undefined : 'invalid'}
                                    id={'organization-invitation-email-input'}
                                />
                                <TextField
                                    minLength={MIN_ORG_NAME}
                                    maxLength={MAX_ORG_NAME}
                                    label={'Organization name'}
                                    aria-label={'Organization name'}
                                    value={organizationName}
                                    onChange={setOrganizationName}
                                    id={'organization-invitation-organization-name-input'}
                                />
                                <ErrorMessage message={error} id={'invite-organization-error'} marginStart={0} />
                                <Divider size={'S'} marginY={'size-200'} />

                                <ButtonGroup align={'end'}>
                                    <Button
                                        variant={'secondary'}
                                        onPress={handleCloseSendInvite}
                                        id={'cancel-organization-invitation-button'}
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        type={'submit'}
                                        variant={'accent'}
                                        isPending={inviteOrganization.isPending}
                                        isDisabled={isSendInviteDisabled}
                                        id={'send-organization-invitation-button'}
                                    >
                                        Send invite
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
