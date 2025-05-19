// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Flex,
    Heading,
    InlineAlert,
    Item,
    Menu,
    Tooltip,
    TooltipTrigger,
    View,
} from '@geti/ui';
import { MenuTrigger as SpectrumMenuTrigger } from '@react-spectrum/menu';
import { OverlayTriggerState } from '@react-stately/overlays';

import { ChevronDownSmall } from '../../../assets/icons';
import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useStatus } from '../../../core/status/hooks/use-status.hook';
import { isBelowTooLowFreeDiskSpace } from '../../../core/status/hooks/utils';
import { useCheckPermission } from '../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../shared/components/has-permission/has-permission.interface';
import { ProjectImportPanel } from '../import-project-panel.component';

import classes from './create-project-button.module.scss';

export enum CreateProjectMenuActions {
    IMPORT_PROJECT = 'Create from exported project',
    IMPORT_DATASET = 'Create from dataset',
}

interface CreateProjectMenuProps {
    openImportDatasetDialog: OverlayTriggerState;
}

const useMenuItems = () => {
    const canImportProjects = useCheckPermission([OPERATION.IMPORT_PROJECT]);
    const items = [{ name: CreateProjectMenuActions.IMPORT_DATASET, id: CreateProjectMenuActions.IMPORT_DATASET }];

    if (canImportProjects) {
        items.push({ name: CreateProjectMenuActions.IMPORT_PROJECT, id: CreateProjectMenuActions.IMPORT_PROJECT });
    }

    return items;
};

export const CreateProjectMenu = ({ openImportDatasetDialog }: CreateProjectMenuProps): JSX.Element => {
    const { data: status } = useStatus();
    const [showImportProjectDialog, setShowImportProjectDialog] = useState(false);

    const { FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT } = useFeatureFlags();

    const disabledKeys = isBelowTooLowFreeDiskSpace(status?.freeSpace ?? 0)
        ? [CreateProjectMenuActions.IMPORT_PROJECT, CreateProjectMenuActions.IMPORT_DATASET]
        : [];

    const onOpenDialog = (key: Key) => {
        switch (key) {
            case CreateProjectMenuActions.IMPORT_PROJECT:
                setShowImportProjectDialog(true);
                break;
            case CreateProjectMenuActions.IMPORT_DATASET:
                openImportDatasetDialog.open();
                break;
        }
    };

    const dismissImportProject = () => {
        setShowImportProjectDialog(false);
    };

    const items = useMenuItems();

    return (
        <>
            <SpectrumMenuTrigger>
                <TooltipTrigger placement={'bottom'}>
                    <Button
                        variant={'accent'}
                        id={'create-project-menu'}
                        aria-label={'Create project menu'}
                        UNSAFE_className={classes.createProjectMenuButton}
                        minWidth={'size-450'}
                    >
                        <ChevronDownSmall />
                    </Button>
                    <Tooltip>Create project menu</Tooltip>
                </TooltipTrigger>

                <Menu items={items} onAction={onOpenDialog} disabledKeys={disabledKeys}>
                    {(item) => <Item>{item.name}</Item>}
                </Menu>
            </SpectrumMenuTrigger>
            {showImportProjectDialog && (
                <DialogContainer onDismiss={dismissImportProject}>
                    <Dialog width={1000} height={800}>
                        <Heading>Import project</Heading>
                        <Divider />
                        <Content UNSAFE_className={classes.dialogContent}>
                            <Flex height='100%' direction='column' gap='size-200'>
                                {FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT && (
                                    <InlineAlert variant='notice'>
                                        <Heading>Importing projects from an external source</Heading>
                                        <Content>
                                            Before importing the project please make sure that the import file is
                                            trustworthy.
                                        </Content>
                                    </InlineAlert>
                                )}

                                <View padding='size-250' backgroundColor='gray-50' height='100%'>
                                    <ProjectImportPanel
                                        options={{
                                            // At the moment we do not allow the user to change these options
                                            // we keep them here though so that it is easy to re-enable them
                                            // in future versions
                                            skipSignatureVerification: true,
                                            keepOriginalDates: false,
                                            projectName: '',
                                        }}
                                        onImportProject={() => {
                                            setShowImportProjectDialog(false);
                                        }}
                                    />
                                </View>
                            </Flex>
                        </Content>
                        <ButtonGroup>
                            <Button variant='secondary' onPress={() => setShowImportProjectDialog(false)}>
                                Cancel
                            </Button>
                        </ButtonGroup>
                    </Dialog>
                </DialogContainer>
            )}
        </>
    );
};
