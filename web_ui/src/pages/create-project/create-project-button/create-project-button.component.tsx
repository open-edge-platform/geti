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

import { Flex, Text } from '@adobe/react-spectrum';
import { OverlayTriggerState } from '@react-stately/overlays';

import { Button } from '../../../shared/components/button/button.component';
import { CreateProjectMenu } from './create-project-menu.component';

import classes from './create-project-button.module.scss';

interface CreateProjectButtonProps {
    buttonText: string;
    handleOpenDialog: () => void;
    openImportDatasetDialog: OverlayTriggerState;
}

export const CreateProjectButton = ({
    buttonText,
    handleOpenDialog,
    openImportDatasetDialog,
}: CreateProjectButtonProps): JSX.Element => {
    return (
        <Flex alignItems={'center'} gap={'size-10'}>
            <Button
                variant='accent'
                id='create-new-project-button'
                onPress={handleOpenDialog}
                UNSAFE_className={classes.createProjectButton}
            >
                <Text marginX='size-100' UNSAFE_style={{ whiteSpace: 'nowrap' }}>
                    {buttonText}
                </Text>
            </Button>
            <CreateProjectMenu openImportDatasetDialog={openImportDatasetDialog} />
        </Flex>
    );
};
