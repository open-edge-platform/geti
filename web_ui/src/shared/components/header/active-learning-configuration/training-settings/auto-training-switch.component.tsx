// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC } from 'react';

import { Divider, Flex, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';

import { useReconfigAutoTraining } from '../../../../../core/configurable-parameters/hooks/use-reconfig-auto-training.hook';
import { useGetRunningJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { RunningJobProps, RunningTrainingJob } from '../../../../../core/jobs/jobs.interface';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { isActiveModel } from '../../../../../core/models/utils';
import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { Task } from '../../../../../core/projects/task.interface';
import { paths } from '../../../../../core/services/routes';
import { useRequiredAnnotations } from '../../../../../pages/annotator/hooks/use-required-annotations.hook';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { formatDate } from '../../../../utils';
import {
    BooleanGroupParams,
    ConfigurableParametersTaskChain,
    NumberGroupParams,
} from '../../../configurable-parameters/configurable-parameters.interface';
import { LinkNewTab } from '../../../link-new-tab/link-new-tab.component';
import { getAllJobs } from '../../jobs-management/utils';
import { ToggleTrainingButton } from '../start-stop-training-button/start-stop-training-button.component';
import { AutoTrainingConfigSwitch } from './auto-training-config-switch.component';
import { AutoTrainingThreshold } from './auto-training-threshold.component';

import classes from '../auto-training.module.scss';

interface AutoTrainingSwitchProps {
    task: Task;
    activeModel?: ModelsGroups;
    projectIdentifier: ProjectIdentifier;
    trainingConfig: BooleanGroupParams | undefined;
    dynamicRequiredAnnotationsConfig: BooleanGroupParams | undefined;
    requiredImagesAutoTrainingConfig?: NumberGroupParams | undefined;
    configParameters: ConfigurableParametersTaskChain[];
    isTaskChainMode: boolean; // project is task chain (project details page) or all tasks mode (annotator page)
}

const hasEqualProjectAndTask = (id: string, taskName: string) => (data: RunningJobProps | RunningTrainingJob) =>
    isEqual(data.metadata.project.id, id) && isEqual((data as RunningTrainingJob).metadata?.task?.name, taskName);

const ActiveModelLink = ({
    projectIdentifier,
    activeModel,
}: {
    projectIdentifier: ProjectIdentifier;
    activeModel: ModelsGroups;
}) => {
    const activeVersion = activeModel?.modelVersions.find(isActiveModel);

    const getModelUrl = (groupId: string, versionId: string) =>
        paths.project.models.model.modelVariants.index({ ...projectIdentifier, groupId, modelId: versionId });

    if (activeVersion === undefined) {
        return null;
    }

    return (
        <Flex direction={'column'}>
            <Text UNSAFE_className={classes.activeModelTitle}>Active model</Text>
            <Text>
                <LinkNewTab
                    ariaLabel={'Active model link'}
                    text={`${activeModel.groupName} - Version ${
                        activeVersion.version
                    } (${formatDate(activeVersion.creationDate, 'DD MMM YY')})`}
                    url={getModelUrl(activeModel.groupId, activeVersion.id)}
                    className={classes.modelLink}
                />
            </Text>
        </Flex>
    );
};

const NewAnnotations = ({ task, newAnnotations }: { task: Task; newAnnotations: number }) => {
    return (
        <Flex gap={'size-100'} alignItems={'center'}>
            <Text id={`new-annotations-${idMatchingFormat(task.title)}`} UNSAFE_className={classes.annotationsTitle}>
                New annotations
            </Text>
            <Text
                justifySelf={'end'}
                id={`new-annotations-value-${idMatchingFormat(task.title)}`}
                UNSAFE_className={classes.newAnnotations}
            >
                {newAnnotations}
            </Text>
        </Flex>
    );
};

export const AutoTrainingSwitch: FC<AutoTrainingSwitchProps> = ({
    task,
    activeModel,
    trainingConfig,
    isTaskChainMode,
    configParameters,
    projectIdentifier,
    dynamicRequiredAnnotationsConfig,
    requiredImagesAutoTrainingConfig,
}) => {
    const [requiredAnnotations] = useRequiredAnnotations(task);
    const autoTrainingOptimisticUpdates = useReconfigAutoTraining(projectIdentifier);

    const { data } = useGetRunningJobs({ projectId: projectIdentifier.projectId });

    const runningTaskJobs = (getAllJobs(data) as RunningTrainingJob[]).filter(
        hasEqualProjectAndTask(projectIdentifier.projectId, task.title)
    );

    const isAutotrainingOn = Boolean(trainingConfig?.value);

    const hasRunningJobs = !isEmpty(runningTaskJobs);

    return (
        <>
            <View
                backgroundColor={isTaskChainMode ? 'gray-100' : undefined}
                padding={isTaskChainMode ? 'size-200' : undefined}
            >
                <Flex gap={'size-150'} direction='column'>
                    {activeModel && <ActiveModelLink projectIdentifier={projectIdentifier} activeModel={activeModel} />}

                    <NewAnnotations task={task} newAnnotations={requiredAnnotations.newAnnotations} />

                    {trainingConfig !== undefined && (
                        <AutoTrainingConfigSwitch
                            task={task}
                            isDisabled={hasRunningJobs}
                            autoTrainingOptimisticUpdates={autoTrainingOptimisticUpdates}
                            configParameters={configParameters}
                            trainingConfig={trainingConfig}
                        />
                    )}

                    {isAutotrainingOn &&
                        requiredImagesAutoTrainingConfig !== undefined &&
                        dynamicRequiredAnnotationsConfig !== undefined && (
                            <AutoTrainingThreshold
                                task={task}
                                autoTrainingOptimisticUpdates={autoTrainingOptimisticUpdates}
                                configParameters={configParameters}
                                requiredImagesAutoTrainingConfig={requiredImagesAutoTrainingConfig}
                                dynamicRequiredAnnotationsConfig={dynamicRequiredAnnotationsConfig}
                            />
                        )}
                </Flex>
            </View>
            <Divider size='S' marginY={'size-200'} />

            <ToggleTrainingButton
                task={task}
                isAutotraining={isAutotrainingOn}
                runningTaskJobs={runningTaskJobs}
                projectIdentifier={projectIdentifier}
            />
        </>
    );
};
