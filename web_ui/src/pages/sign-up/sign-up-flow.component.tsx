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

import { FormEvent, ReactNode } from 'react';

import { ButtonGroup, Divider, Flex, Form, Heading } from '@adobe/react-spectrum';

import { Button } from '../../shared/components/button/button.component';
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
