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

import { useRef } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';

import { InfoOutline } from '../../../../../assets/icons';
import { useStatus } from '../../../../../core/status/hooks/use-status.hook';
import { isBelowTooLowFreeDiskSpace } from '../../../../../core/status/hooks/utils';
import { ProjectImportBase } from '../../../../../providers/projects-import-provider/project-import.interface';
import { useProjectsImportProvider } from '../../../../../providers/projects-import-provider/projects-import-provider.component';
import { MenuTriggerButton } from '../../../../../shared/components/menu-trigger/menu-trigger-button/menu-trigger-button.component';
import {
    ColorMode,
    QuietActionButton,
} from '../../../../../shared/components/quiet-button/quiet-action-button.component';
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
                <QuietActionButton
                    colorMode={ColorMode.DARK}
                    onPress={onTryAgain}
                    isDisabled={isTryAgainButtonDisabled}
                >
                    Try again
                </QuietActionButton>
            </Flex>
            <ProjectImportFilePicker ref={fileRef} options={importItem.options} />
        </>
    );
};
