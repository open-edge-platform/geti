// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, FormEvent, ReactNode, useState } from 'react';

import { ButtonGroup, Divider, Flex, Form, Heading, TextField } from '@adobe/react-spectrum';

import { Button } from '../../shared/components/button/button.component';
import { InvalidTokenAlert } from '../../shared/components/invalid-token-alert/invalid-token-alert.component';
import { Container } from './container.component';
import { RegistrationError } from './registration-error.component';
import { TermsAndConditions } from './terms-and-conditions.component';

import classes from './request-access-flow.module.scss';

interface RequestAccessDialogProps {
    isOpen: boolean;
    organizationField?: ReactNode;
    hasError: boolean;
    isLoading: boolean;
    onSubmit: (requestAccessReason: string) => (event: FormEvent<HTMLFormElement>) => void;
    isSubmitButtonDisabled: boolean;
    isChecked: boolean;
    onCheckedChange: (checked: boolean) => void;
    isExpiredToken: boolean;
}

export const RequestAccessFlow: FC<RequestAccessDialogProps> = ({
    isOpen,
    onSubmit,
    isLoading,
    isSubmitButtonDisabled,
    isChecked,
    onCheckedChange,
    organizationField,
    hasError,
    isExpiredToken,
}) => {
    const [requestAccessReason, setRequestAccessReason] = useState<string>('');

    return (
        <Container title={"Let's complete your registration to Intel® Geti™!"} isOpen={isOpen}>
            <Form onSubmit={onSubmit(requestAccessReason)}>
                <Flex direction={'column'} gap={'size-200'}>
                    <Heading level={3} margin={0} marginBottom={'size-200'} UNSAFE_className={classes.heading}>
                        You are trying to access Intel® Geti™ but you are not a registered user. Would you like to
                        request access?
                    </Heading>

                    <Heading level={6} margin={0}>
                        Please provide the following details to complete your registration.
                    </Heading>

                    {organizationField}

                    <TextField
                        width={'100%'}
                        label={'For what use case do you plan to use Intel® Geti™?'}
                        value={requestAccessReason}
                        onChange={setRequestAccessReason}
                        placeholder={'Please describe your use case (optional)'}
                    />

                    <Divider size={'S'} />

                    <TermsAndConditions isChecked={isChecked} onCheckedChange={onCheckedChange} />

                    {hasError ? <RegistrationError /> : <></>}

                    <InvalidTokenAlert isVisible={isExpiredToken} message={'Your invitation link has expired'} />

                    <ButtonGroup width={'100%'} align={'end'}>
                        <Button
                            type='submit'
                            variant={'accent'}
                            id={'submit-button'}
                            isPending={isLoading}
                            isDisabled={isSubmitButtonDisabled}
                        >
                            Request access
                        </Button>
                    </ButtonGroup>
                </Flex>
            </Form>
        </Container>
    );
};
