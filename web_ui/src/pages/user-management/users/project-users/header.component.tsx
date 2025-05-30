// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Button, DialogContainer, Flex } from '@geti/ui';

import { AddUserToProjectDialog } from './add-user-to-project.component';

export const Header = () => {
    const [isOpen, setIsOpen] = useState<boolean>(false);

    const handleClose = (): void => {
        setIsOpen(false);
    };

    return (
        <Flex alignItems={'center'} gap={'size-150'}>
            <Button
                variant='primary'
                onPress={() => setIsOpen(true)}
                id='add-user-button-id'
                aria-label={'add user to project'}
            >
                Add user to project
            </Button>

            <DialogContainer onDismiss={() => setIsOpen(false)}>
                {isOpen && <AddUserToProjectDialog onClose={handleClose} />}
            </DialogContainer>
        </Flex>
    );
};
