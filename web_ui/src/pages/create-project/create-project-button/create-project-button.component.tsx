// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Flex, Text } from '@geti/ui';
import { OverlayTriggerState } from '@react-stately/overlays';

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
