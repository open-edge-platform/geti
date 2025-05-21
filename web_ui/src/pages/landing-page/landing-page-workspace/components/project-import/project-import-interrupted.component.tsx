// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { ActionButton, ColorMode, Flex, Text } from '@geti/ui';
import { InfoOutline } from '@geti/ui/icons';

import { useStatus } from '../../../../../core/status/hooks/use-status.hook';
import { isBelowTooLowFreeDiskSpace } from '../../../../../core/status/hooks/utils';
import { ProjectImportBase } from '../../../../../providers/projects-import-provider/project-import.interface';
import { useProjectsImportProvider } from '../../../../../providers/projects-import-provider/projects-import-provider.component';
import { MenuTriggerButton } from '../../../../../shared/components/menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { ProjectImportFilePicker } from './project-import-file-picker.component';
import { ProjectStatusHeader } from './project-status-header.component';

import classes from './project-import.module.scss';

interface ProjectImportInterruptedProps {
    importItem: ProjectImportBase;
}

export const ProjectImportInterrupted = ({ importItem }: ProjectImportInterruptedProps): JSX.Element => {
    const { data: status } = useStatus();
    const isTryAgainButtonDisabled = isBelowTooLowFreeDiskSpace(status?.freeSpace);

    const { fileId, fileName, fileSize } = importItem;
    const fileRef = useRef<HTMLInputElement>(null);
    const { removeImportProjectItemFromLS } = useProjectsImportProvider();

    const onTryAgain = (): void => {
        fileRef.current?.click();
    };

    return (
        <>
            <ProjectStatusHeader
                fileName={fileName}
                fileSize={fileSize}
                menuActions={
                    <MenuTriggerButton
                        isQuiet
                        items={['Delete']}
                        onAction={() => removeImportProjectItemFromLS(fileId)}
                        id='import-project-action-menu'
                    />
                }
            />
            <Flex
                gap={'size-100'}
                alignItems='center'
                justifyContent={'space-between'}
                UNSAFE_className={classes.importContent}
            >
                <Flex alignItems={'center'} gap={'size-150'}>
                    <InfoOutline />
                    <Text>Importing has been interrupted</Text>
                </Flex>
                <ActionButton
                    isQuiet
                    colorMode={ColorMode.DARK}
                    onPress={onTryAgain}
                    isDisabled={isTryAgainButtonDisabled}
                >
                    Try again
                </ActionButton>
            </Flex>
            <ProjectImportFilePicker ref={fileRef} options={importItem.options} />
        </>
    );
};
