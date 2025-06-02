// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { FORBIDDEN_MESSAGE } from '@geti/core/src/services/utils';
import { Button, ButtonGroup, Content, Flex, Heading, Text } from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { Forbidden } from '../../../assets/images';

import classes from './access-denied.module.scss';

interface AccessDeniedDialogProps {
    onReset: () => void;
}

export const AccessDenied = ({ onReset }: AccessDeniedDialogProps): JSX.Element => {
    const navigate = useNavigate();

    const handleGoHome = () => {
        onReset();

        navigate(paths.root({}), { replace: true });
    };

    return (
        <>
            <Content marginBottom={'size-150'}>
                <Flex direction={'column'} alignItems={'center'}>
                    <Heading UNSAFE_className={classes.accessDeniedCode} marginY={0}>
                        <Forbidden />
                    </Heading>
                    <Heading UNSAFE_className={classes.accessDeniedText} marginY={0}>
                        Forbidden
                    </Heading>
                    <Text>{FORBIDDEN_MESSAGE}</Text>
                </Flex>
            </Content>
            <ButtonGroup UNSAFE_className={classes.accessDeniedButtonGroup}>
                <Button variant={'accent'} onPress={handleGoHome}>
                    Go to home page
                </Button>
            </ButtonGroup>
        </>
    );
};
