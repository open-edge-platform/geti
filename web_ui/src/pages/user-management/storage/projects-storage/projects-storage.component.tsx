// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { Flex } from '@adobe/react-spectrum';

import { CardContent } from '../../../../shared/components/card-content/card-content.component';
import { FullscreenAction } from '../../../../shared/components/fullscreen-action/fullscreen-action.component';
import { ProjectStorageContent } from './project-storage-content.component';
import { ProjectStorageToggleButton } from './project-storage-toggle-button.component';

export const ProjectsStorage = () => {
    const [isProjectsListViewVisible, setIsProjectsListViewVisible] = useState<boolean>(true);

    const handleProjectStorageToggle = () => {
        setIsProjectsListViewVisible((prevState) => !prevState);
    };

    return (
        <CardContent
            title='Usage per project'
            height={'100%'}
            actions={
                <Flex>
                    <ProjectStorageToggleButton
                        onPress={handleProjectStorageToggle}
                        isProjectsListViewVisible={isProjectsListViewVisible}
                    />

                    <FullscreenAction
                        title='Usage per project'
                        actionButton={
                            <ProjectStorageToggleButton
                                onPress={handleProjectStorageToggle}
                                isProjectsListViewVisible={isProjectsListViewVisible}
                            />
                        }
                    >
                        <ProjectStorageContent isProjectsListViewVisible={isProjectsListViewVisible} />
                    </FullscreenAction>
                </Flex>
            }
        >
            <ProjectStorageContent isProjectsListViewVisible={isProjectsListViewVisible} />
        </CardContent>
    );
};
