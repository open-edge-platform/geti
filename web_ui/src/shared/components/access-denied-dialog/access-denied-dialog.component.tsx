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

import { ButtonGroup, Content, Dialog, DialogContainer, Flex, Heading, Text } from '@adobe/react-spectrum';
import { useNavigate } from 'react-router-dom';

import { Forbidden } from '../../../assets/images';
import { paths } from '../../../core/services/routes';
import { FORBIDDEN_MESSAGE } from '../../../core/services/utils';
import { Button } from '../button/button.component';

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
