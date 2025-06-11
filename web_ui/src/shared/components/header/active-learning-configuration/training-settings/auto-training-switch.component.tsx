// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { paths } from '@geti/core';
import { Divider, Flex, Text, View } from '@geti/ui';
import { isEmpty, isEqual } from 'lodash-es';

import {
    BooleanGroupParams,
    NumberGroupParams,
} from '../../../../../core/configurable-parameters/services/configurable-parameters.interface';
import {
    BoolParameter,
    NumberParameter,
} from '../../../../../core/configurable-parameters/services/configuration.interface';
import { useGetRunningJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { RunningJobProps, RunningTrainingJob } from '../../../../../core/jobs/jobs.interface';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { isActiveModel } from '../../../../../core/models/utils';
import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { Task } from '../../../../../core/projects/task.interface';
import { useRequiredAnnotations } from '../../../../../pages/annotator/hooks/use-required-annotations.hook';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { formatDate } from '../../../../utils';
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
    trainingConfig: BooleanGroupParams | BoolParameter | undefined;
    dynamicRequiredAnnotationsConfig: BooleanGroupParams | BoolParameter | undefined;
    requiredImagesAutoTrainingConfig?: NumberGroupParams | NumberParameter | undefined;
    onUpdateRequiredImagesAutoTraining: (value: number) => void;
    onUpdateDynamicRequiredAnnotations: (value: boolean) => void;
    onUpdateAutoTraining: (value: boolean) => void;
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
    projectIdentifier,
    dynamicRequiredAnnotationsConfig,
    requiredImagesAutoTrainingConfig,
    onUpdateAutoTraining,
    onUpdateRequiredImagesAutoTraining,
    onUpdateDynamicRequiredAnnotations,
}) => {
    const [requiredAnnotations] = useRequiredAnnotations(task);

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
                            isAutoTrainingEnabled={trainingConfig.value}
                            onAutoTraining={onUpdateAutoTraining}
                        />
                    )}

                    {isAutotrainingOn &&
                        requiredImagesAutoTrainingConfig !== undefined &&
                        dynamicRequiredAnnotationsConfig !== undefined && (
                            <AutoTrainingThreshold
                                requiredImagesAutoTrainingConfig={requiredImagesAutoTrainingConfig}
                                dynamicRequiredAnnotations={dynamicRequiredAnnotationsConfig.value}
                                onUpdateDynamicRequiredAnnotations={onUpdateDynamicRequiredAnnotations}
                                onUpdateRequiredAnnotations={onUpdateRequiredImagesAutoTraining}
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
