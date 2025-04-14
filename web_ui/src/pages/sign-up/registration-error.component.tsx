// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
