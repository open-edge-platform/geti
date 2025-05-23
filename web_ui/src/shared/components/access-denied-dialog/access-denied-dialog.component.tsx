// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { FORBIDDEN_MESSAGE } from '@geti/core/src/services/utils';
import { Button, ButtonGroup, Content, Dialog, DialogContainer, Flex, Heading, Text } from '@geti/ui';
import { useNavigate } from 'react-router-dom';

import { Forbidden } from '../../../assets/images';

import classes from './access-denied-dialog.module.scss';

interface AccessDeniedDialogProps {
    isOpen: boolean;
    handleClose: () => void;
}

export const AccessDeniedDialog = ({ isOpen, handleClose }: AccessDeniedDialogProps): JSX.Element => {
    const navigate = useNavigate();

    const handleGoHome = () => {
        handleClose();

        navigate(paths.root({}), { replace: true });
    };

    return (
        <DialogContainer onDismiss={handleClose}>
            {isOpen && (
                <Dialog zIndex={999999}>
                    <Content>
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
                </Dialog>
            )}
        </DialogContainer>
    );
};
