// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, Flex, Heading, Link as SpectrumLink, Text } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';
import { Link, useNavigate } from 'react-router-dom';

import { ServiceUnavailableIcon } from '../../assets/images';
import { ErrorLayout } from '../../pages/errors/error-layout/error-layout.component';

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
