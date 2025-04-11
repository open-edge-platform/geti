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

import { LinkExpiredImage } from '../../../assets/images';
import { paths } from '../../../core/services/routes';
import { Button } from '../../../shared/components/button/button.component';
import { CustomerSupportLink } from '../../../shared/components/customer-support-link/customer-support-link.component';
import { redirectTo } from '../../../shared/utils';

import classes from '../error-layout/error-layout.module.scss';

export const BadRequest = (): JSX.Element => {
    return (
        <>
            <LinkExpiredImage aria-label={'Bad request'} />
            <Heading UNSAFE_className={classes.errorMessageHeader} data-testid={'bad-request-id'}>
                Bad request
            </Heading>
            <Content UNSAFE_className={classes.errorMessage}>
                <Text UNSAFE_style={{ display: 'block' }}>
                    The server cannot or will not process the current request.
                </Text>
                <Text UNSAFE_style={{ display: 'block' }}>
                    If the problem persists, please contact <CustomerSupportLink />.
                </Text>
            </Content>
            <Button
                variant={'accent'}
                marginTop={'size-200'}
                onPress={() => {
                    redirectTo(paths.root({}));
                }}
            >
                Go back to home
            </Button>
        </>
    );
};
