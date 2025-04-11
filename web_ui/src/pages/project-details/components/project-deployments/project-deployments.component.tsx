// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMemo, useState } from 'react';

import { DialogContainer, Flex } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import uniqBy from 'lodash/uniqBy';

import { DeploymentImg } from '../../../../assets/images';
import { isVisualPromptModelGroup } from '../../../../core/annotations/services/visual-prompt-service';
import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { Button } from '../../../../shared/components/button/button.component';
import { TooltipWithDisableButton } from '../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
import { TutorialCardBuilder } from '../../../../shared/components/tutorial-card/tutorial-card-builder.component';
import { isNotCropTask } from '../../../../shared/utils';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { NO_MODELS_MESSAGE, NO_MODELS_MESSAGE_TASK_CHAIN } from '../../utils';
import { DownloadDialogSingleTask } from './download-dialog-single-task.component';
import { DownloadDialogTaskChain } from './download-dialog-task-chain.component';

import classes from './project-deployments.module.scss';

const TEXT_FIRST_LINE = 'Once you tested and optimized the model, ';
const TEXT_SECOND_LINE = 'you are ready to download and deploy your solution.';

/* 
    Main component for Project Deployments.
    
    This component is responsible for running the code deployment queries and to initialize
    the download.

    It renders the main screen plus 2 download dialogs, depending on the project type
*/
export const ProjectDeployments = (): JSX.Element => {
    const [isDownloadDialogOpen, setIsDownloadDialogOpen] = useState<boolean>(false);

    const {
        project: { tasks },
        isTaskChainProject,
        projectIdentifier,
    } = useProject();

    const { useModelsQuery } = useModels();
    const { data: modelsGroupsData, isLoading: isLoadingModelGroups } = useModelsQuery(projectIdentifier);
    const modelsGroups = useMemo(() => {
        return modelsGroupsData?.filter((group) => isVisualPromptModelGroup(group) === false) ?? [];
    }, [modelsGroupsData]);

    const tasksWithoutCropTask = tasks.filter(isNotCropTask);

    const handleCloseDialog = () => {
        setIsDownloadDialogOpen(false);
    };

    const isDeploymentDisabled = useMemo(() => {
        if (isEmpty(modelsGroups)) {
            return true;
        }

        if (isTaskChainProject) {
            return !(uniqBy(modelsGroups, (group) => group.taskId).length === tasksWithoutCropTask.length);
        }

        return false;
    }, [isTaskChainProject, modelsGroups, tasksWithoutCropTask.length]);

    const buttonTooltipMessage = isDeploymentDisabled
        ? isTaskChainProject
            ? NO_MODELS_MESSAGE_TASK_CHAIN
            : NO_MODELS_MESSAGE
        : '';

    return (
        <PageLayout breadcrumbs={[{ id: 'deployments-id', breadcrumb: 'Deployments' }]}>
            <>
                <TutorialCardBuilder cardKey={TUTORIAL_CARD_KEYS.PROJECT_DEPLOYMENT_TUTORIAL} />
                <Flex
                    direction={'column'}
                    alignItems={'center'}
                    justifyContent={'center'}
                    height={'100%'}
                    width={'100%'}
                >
                    <>
                        <DeploymentImg className={classes.illustration} />

                        <Flex
                            direction={'column'}
                            alignItems={'center'}
                            justifyContent={'center'}
                            marginTop={'size-250'}
                        >
                            <span>{TEXT_FIRST_LINE}</span>
                            <span>{TEXT_SECOND_LINE}</span>
                        </Flex>

                        <>
                            <TooltipWithDisableButton placement={'top'} disabledTooltip={buttonTooltipMessage}>
                                <Button
                                    variant={'accent'}
                                    marginTop={'size-200'}
                                    isPending={isLoadingModelGroups}
                                    isDisabled={isDeploymentDisabled}
                                    id={'select-model-deployment-id'}
                                    onPress={() => setIsDownloadDialogOpen(true)}
                                >
                                    Select model for deployment
                                </Button>
                            </TooltipWithDisableButton>

                            <DialogContainer onDismiss={handleCloseDialog}>
                                {isDownloadDialogOpen &&
                                    (isTaskChainProject ? (
                                        <DownloadDialogTaskChain
                                            projectIdentifier={projectIdentifier}
                                            tasks={tasksWithoutCropTask}
                                            close={handleCloseDialog}
                                            modelsGroups={modelsGroups}
                                        />
                                    ) : (
                                        <DownloadDialogSingleTask
                                            projectIdentifier={projectIdentifier}
                                            task={tasks[0]}
                                            close={handleCloseDialog}
                                            modelsGroups={modelsGroups}
                                        />
                                    ))}
                            </DialogContainer>
                        </>
                    </>
                </Flex>
            </>
        </PageLayout>
    );
};
