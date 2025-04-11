// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { DialogContainer, Flex } from '@adobe/react-spectrum';

import { Button } from '../../../../shared/components/button/button.component';
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
