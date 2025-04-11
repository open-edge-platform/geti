// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Content, Flex, Heading, Link as SpectrumLink, Text } from '@adobe/react-spectrum';
import { Link, useNavigate } from 'react-router-dom';

import { ServiceUnavailableIcon } from '../../assets/images';
import { ErrorLayout } from '../../pages/errors/error-layout/error-layout.component';
import { Button } from '../../shared/components/button/button.component';

export const LogoutRoute = ({ home }: { home: string }): JSX.Element => {
    const navigate = useNavigate();

    const handleGoHome = () => {
        navigate(home);
    };

    return (
        <ErrorLayout>
            <ServiceUnavailableIcon aria-label={'Logout screen'} />
            <Heading data-testid={'logout-screen-id'}>Logout successful</Heading>
            <Content>
                <Flex direction={'column'} alignItems={'center'}>
                    <Text>
                        You can now close this window, or{' '}
                        <SpectrumLink>
                            <Link to={home}>log in</Link>
                        </SpectrumLink>{' '}
                        again.
                    </Text>
                </Flex>
            </Content>
            <Button variant={'accent'} marginTop={'size-200'} onPress={handleGoHome}>
                Login
            </Button>
        </ErrorLayout>
    );
};
