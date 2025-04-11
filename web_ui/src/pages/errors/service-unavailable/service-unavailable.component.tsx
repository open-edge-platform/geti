// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Content, Heading, Text } from '@adobe/react-spectrum';

import { ConnectionLost } from '../../../assets/images';
import { CustomerSupportLink } from '../../../shared/components/customer-support-link/customer-support-link.component';

import classes from '../error-layout/error-layout.module.scss';

export const ServiceUnavailable = (): JSX.Element => {
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
