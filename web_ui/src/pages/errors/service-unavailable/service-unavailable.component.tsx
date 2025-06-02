// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Content, Heading, Text } from '@geti/ui';

import { ConnectionLost } from '../../../assets/images';
import { CustomerSupportLink } from '../../../shared/components/customer-support-link/customer-support-link.component';

import classes from '../error-layout/error-layout.module.scss';

export const ServiceUnavailable: FC = () => {
    return (
        <>
            <ConnectionLost />
            <Heading UNSAFE_className={classes.errorMessageHeader} data-testid={'server-connection-lost-id'}>
                We are experiencing technical difficulties
            </Heading>
            <Content UNSAFE_className={classes.errorMessage}>
                <Text UNSAFE_style={{ display: 'block' }} marginBottom={'size-100'}>
                    We apologize for the inconvenience, but we are currently experiencing technical difficulties. Our
                    team is actively working to resolve the issue and restore full functionality as quickly as possible.
                </Text>
                <Text>
                    If you require immediate assistance or have any urgent concerns, please do not hesitate to reach out
                    to our <CustomerSupportLink /> team.
                </Text>
            </Content>
        </>
    );
};
