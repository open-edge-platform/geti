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

import { Content, Heading, InlineAlert, Text } from '@adobe/react-spectrum';

import { CustomerSupportLink } from '../../shared/components/customer-support-link/customer-support-link.component';

export const RegistrationError: FC = () => {
    return (
        <InlineAlert variant='negative' width={'100%'}>
            <Heading>Something went wrong when completing the registration</Heading>
            <Content>
                <Text>
                    Please contact <CustomerSupportLink />.
                </Text>
            </Content>
        </InlineAlert>
    );
};
