// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Flex } from '@geti/ui';

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
