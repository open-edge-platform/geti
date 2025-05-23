// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { paths } from '@geti/core';
import { Heading } from '@geti/ui';
import { Navigate } from 'react-router-dom';

import { Container } from './container.component';
import { useShowRequestAccessConfirmation } from './use-show-request-access-confirmation.hook';

export const RequestAccessConfirmation: FC = () => {
    const showRequestAccessConfirmation = useShowRequestAccessConfirmation();

    if (!showRequestAccessConfirmation) {
        return <Navigate to={paths.root({})} replace />;
    }

    return (
        <Container title={'Intel® Geti™ registration completed!'} isOpen>
            <Heading
                margin={0}
                UNSAFE_style={{
                    textAlign: 'center',
                }}
            >
                Thank you for your interest in Intel® Geti™.
            </Heading>
            <Heading
                UNSAFE_style={{
                    textAlign: 'center',
                }}
            >
                Your access request has been submitted and will be processed as soon as possible.
            </Heading>
        </Container>
    );
};
