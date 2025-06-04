// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Heading,
    Loading,
    Text,
    Tooltip,
    TooltipTrigger,
} from '@geti/ui';

import { ConfigurableParametersType } from '../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import { ConfigurableParameters } from '../../../../../shared/components/configurable-parameters/configurable-parameters.component';
import { useReconfigureParametersValue } from './use-reconfigure-parameters-value/use-reconfigure-parameters-value';

import sharedClasses from '../../../../../shared/shared.module.scss';
import classes from './reconfigure-models.module.scss';

export const ReconfigureModels = (): JSX.Element => {
    const [isOpen, setIsOpen] = useState<boolean>(false);
    const {
        configParameters,
        isLoading,
        setIsQueryEnabled,
        isReconfigureButtonDisabled,
        reconfigure,
        isReconfiguring,
        setSelectedComponentId,
        selectedComponent,
        selectedComponentId,
        updateParameter,
    } = useReconfigureParametersValue();

    const handleOpen = (): void => {
        setIsOpen(true);
    };

    const handleOnDismiss = (): void => {
        setIsOpen(false);
        setSelectedComponentId(undefined);
    };

    useEffect(() => {
        setIsQueryEnabled(isOpen);
    }, [isOpen, setIsQueryEnabled]);

    return (
        <>
            <TooltipTrigger placement={'bottom'}>
                <Button variant={'primary'} onPress={handleOpen}>
                    Reconfigure active model
                </Button>
                <Tooltip>Update the configurable parameters for the next round of automatic training</Tooltip>
            </TooltipTrigger>

            <DialogContainer onDismiss={handleOnDismiss}>
                {isOpen && (
                    <Dialog height='90vh' minWidth={{ base: 'auto', L: '90rem' }} width={'80vw'}>
                        <Heading>Reconfigure parameters for active model</Heading>
                        <Divider />
                        <Content UNSAFE_className={sharedClasses.dialogContent}>
                            {isLoading ? (
                                <Loading />
                            ) : configParameters ? (
                                <ConfigurableParameters
                                    type={ConfigurableParametersType.MANY_CONFIG_PARAMETERS}
                                    configParametersData={configParameters}
                                    selectedComponent={selectedComponent}
                                    selectedComponentId={selectedComponentId}
                                    setSelectedComponentId={setSelectedComponentId}
                                    updateParameter={updateParameter}
                                />
                            ) : (
                                <></>
                            )}
                        </Content>
                        <ButtonGroup UNSAFE_className={classes.reconfigureActionButtons}>
                            <Button variant={'secondary'} id={'cancel-button-id'} onPress={handleOnDismiss}>
                                Cancel
                            </Button>
                            <Button
                                variant={'accent'}
                                id={'start-reconfiguration-button-id'}
                                onPress={() => reconfigure(handleOnDismiss)}
                                isDisabled={isReconfigureButtonDisabled}
                            >
                                <Flex alignItems={'center'} gap={'size-65'}>
                                    {isReconfiguring ? <Loading mode='inline' size={'S'} /> : <></>}
                                    <Text>Reconfigure</Text>
                                </Flex>
                            </Button>
                        </ButtonGroup>
                    </Dialog>
                )}
            </DialogContainer>
        </>
    );
};
