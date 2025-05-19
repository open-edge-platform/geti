// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    Tooltip,
    TooltipTrigger,
    View,
} from '@adobe/react-spectrum';
import { LoadingIndicator } from '@geti/ui';
import { isNil } from 'lodash-es';

import { AutoTraining } from '../../../../assets/icons';
import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { Task } from '../../../../core/projects/task.interface';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { ColorMode, QuietActionButton } from '../../quiet-button/quiet-action-button.component';
import { ActiveLearningConfigurationContent } from './active-learning-configuration-content.component';
import { useAutoTrainingTasksConfig } from './use-tasks-auto-training-config.hook';
import { AutoTrainingTask, getAllAutoTrainingValue, getNotificationConfig } from './util';

import classes from './auto-training.module.scss';

export const CornerIndicator = ({ autoTrainingTasks }: { autoTrainingTasks: AutoTrainingTask[] }) => {
    const { isVisible, styles, text } = getNotificationConfig(getAllAutoTrainingValue(autoTrainingTasks));

    return (
        <div style={styles} className={classes.cornerIndicator} aria-label={`Active learning configuration ${text}`}>
            {isVisible && text}
        </div>
    );
};

const ActiveLearningConfigurationDialog = ({ selectedTask }: { selectedTask: Task | null }) => {
    const { project, projectIdentifier } = useProject();
    const { useProjectModelsQuery } = useModels();
    const { isLoading: isLoadingModels } = useProjectModelsQuery();
    const { isLoading } = useAutoTrainingTasksConfig(projectIdentifier, project.tasks);

    const isLoadingData = isLoading || isLoadingModels;

    return (
        <Dialog width={'size-6000'}>
            <Heading id={'active-learning-configuration-header'}>Active learning configuration</Heading>
            <Divider />
            <Content>
                {isLoadingData ? (
                    <View height='size-1600'>
                        <Flex height='100%' alignItems='center' justifyContent={'center'}>
                            <LoadingIndicator />
                        </Flex>
                    </View>
                ) : (
                    <ActiveLearningConfigurationContent selectedTask={selectedTask} />
                )}
            </Content>
        </Dialog>
    );
};

interface ActiveLearningConfigurationProps {
    isDarkMode?: boolean;
    selectedTask: Task | null;
}

export const ActiveLearningConfiguration = ({
    isDarkMode = false,
    selectedTask,
}: ActiveLearningConfigurationProps): JSX.Element => {
    const { project, projectIdentifier } = useProject();
    const { autoTrainingTasks, isLoading, configParameters } = useAutoTrainingTasksConfig(
        projectIdentifier,
        project.tasks
    );

    const filteredTaskAutoTraining = autoTrainingTasks.filter(({ task }) => task.id === selectedTask?.id);
    const filteredAutoTrainingTask = isNil(selectedTask) ? autoTrainingTasks : filteredTaskAutoTraining;

    return (
        <DialogTrigger type='popover' hideArrow>
            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    width={15}
                    isDisabled={isLoading}
                    id={'active-learning-configuration-button'}
                    aria-label={'Active learning configuration'}
                    colorMode={isDarkMode ? ColorMode.DARK : ColorMode.LIGHT}
                    zIndex={1}
                >
                    <AutoTraining width={15} aria-label={'tasks in progress'} />
                    {configParameters && <CornerIndicator autoTrainingTasks={filteredAutoTrainingTask} />}
                </QuietActionButton>

                <Tooltip>Active learning configuration</Tooltip>
            </TooltipTrigger>
            <ActiveLearningConfigurationDialog selectedTask={selectedTask} />
        </DialogTrigger>
    );
};
