// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Heading } from '@adobe/react-spectrum';
import { Navigate } from 'react-router-dom';

import { paths } from '../../core/services/routes';
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
