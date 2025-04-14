// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
