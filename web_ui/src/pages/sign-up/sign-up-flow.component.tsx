// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, ReactNode } from 'react';

import { ButtonGroup, Divider, Flex, Form, Heading } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';

import { InvalidTokenAlert } from '../../shared/components/invalid-token-alert/invalid-token-alert.component';
import { Container } from './container.component';
import { RegistrationError } from './registration-error.component';
import { TermsAndConditions } from './terms-and-conditions.component';

interface SignUpDialogOldFlowProps {
    organizationField?: ReactNode;
    hasError: boolean;
    isLoading: boolean;
    isOpen: boolean;
    onSubmit: (event: FormEvent<HTMLFormElement>) => void;
    isSubmitButtonDisabled: boolean;
    isChecked: boolean;
    onCheckedChange: (checked: boolean) => void;
    isExpiredToken: boolean;
}

export const SignUpFlow = ({
    isExpiredToken,
    organizationField,
    hasError,
    isOpen,
    onSubmit,
    isLoading,
    isSubmitButtonDisabled,
    isChecked,
    onCheckedChange,
}: SignUpDialogOldFlowProps) => {
    return (
        <Container title={"Let's complete your registration to Intel® Geti™!"} isOpen={isOpen}>
            <Form onSubmit={onSubmit}>
                <Flex direction={'column'} UNSAFE_style={{ padding: 'size-300', paddingTop: 0 }} gap={'size-200'}>
                    <Heading level={6} margin={0}>
                        Please provide the following details.
                    </Heading>

                    {organizationField}

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
                            Submit
                        </Button>
                    </ButtonGroup>
                </Flex>
            </Form>
        </Container>
    );
};
