// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { paths } from '@geti/core';
import { Button, Content, Heading, Text } from '@geti/ui';

import { ConnectionLost } from '../../../assets/images';
import { CustomerSupportLink } from '../../../shared/components/customer-support-link/customer-support-link.component';
import { redirectTo } from '../../../shared/utils';

import classes from '../error-layout/error-layout.module.scss';

interface InternalServerErrorProps {
    onReset: () => void;
}

export const InternalServerError: FC<InternalServerErrorProps> = ({ onReset }) => {
    return (
        <>
            <ConnectionLost />
            <Heading UNSAFE_className={classes.errorMessageHeader} data-testid={'bad-request-id'}>
                Internal server error
            </Heading>
            <Content UNSAFE_className={classes.errorMessage}>
                <Text UNSAFE_style={{ display: 'block' }}>
                    The server encountered an error and could not complete your request.
                </Text>
                <Text>
                    If the problem persists, please contact <CustomerSupportLink />.
                </Text>
            </Content>
            <Button
                variant={'accent'}
                marginTop={'size-200'}
                onPress={() => {
                    onReset();
                    redirectTo(paths.root({}));
                }}
            >
                Go back to home
            </Button>
        </>
    );
};
