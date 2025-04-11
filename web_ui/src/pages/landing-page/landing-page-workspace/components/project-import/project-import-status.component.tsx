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

import { Flex, Text } from '@adobe/react-spectrum';

import {
    ProjectImportBase,
    ProjectImportingStatus,
} from '../../../../../providers/projects-import-provider/project-import.interface';
import { useProjectsImportProvider } from '../../../../../providers/projects-import-provider/projects-import-provider.component';
import { LoadingIndicator } from '../../../../../shared/components/loading/loading-indicator.component';
import { MenuTriggerButton } from '../../../../../shared/components/menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { ProgressBar } from '../../../../../shared/components/progress-bar/progress-bar.component';
import { ProjectStatusHeader } from './project-status-header.component';

import classes from './project-import.module.scss';

interface ProjectImportStatusProps {
    importItem: ProjectImportingStatus & ProjectImportBase;
}

export const ProjectImportStatus = ({ importItem }: ProjectImportStatusProps) => {
    const { progress, bytesRemaining, timeRemaining, fileName, fileSize, fileId } = importItem;
    const { cancelImportProject } = useProjectsImportProvider();

    return (
        <>
            <ProjectStatusHeader
                fileName={fileName}
                fileSize={fileSize}
                menuActions={
                    <MenuTriggerButton
                        isQuiet
                        items={['Cancel']}
                        id='import-project-action-menu'
                        ariaLabel='import status menu'
                        onAction={() => cancelImportProject(fileId)}
                    />
                }
            />
            <Flex gap={'size-100'} alignItems='center' UNSAFE_className={classes.importContent}>
                <LoadingIndicator size={'S'} marginEnd={'size-200'} />
                <Flex gap='size-400' flex={1}>
                    <Text>Uploading...</Text>
                    <Flex flex={1} justifyContent={'end'} gap='size-250'>
                        <Text UNSAFE_className={classes.minWidth}>{`${progress}%`}</Text>
                        <Text UNSAFE_className={classes.remaining}>{bytesRemaining}</Text>
                        <Text UNSAFE_className={classes.remaining}>{timeRemaining}</Text>
                    </Flex>
                </Flex>
            </Flex>
            <ProgressBar
                size={'S'}
                showValueLabel={false}
                value={progress}
                aria-label='job-item-progress-bar'
                UNSAFE_className={classes.progressBar}
            />
        </>
    );
};
