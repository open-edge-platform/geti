// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    ActionButton,
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    LoadingIndicator,
    Tooltip,
    TooltipTrigger,
    View,
} from '@geti/ui';
import { AutoTraining } from '@geti/ui/icons';
import { isNil } from 'lodash-es';

import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { Task } from '../../../../core/projects/task.interface';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { ActiveLearningConfigurationContent } from './active-learning-configuration-content.component';
import { useActiveLearningConfiguration } from './use-active-learning-configuration.hook';
import { getAllAutoTrainingValue, getNotificationConfig } from './util';

import classes from './auto-training.module.scss';

export const CornerIndicator = ({ allAutoTrainingValues }: { allAutoTrainingValues: boolean[] }) => {
    const { isVisible, styles, text } = getNotificationConfig(getAllAutoTrainingValue(allAutoTrainingValues));

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
    const { isPending } = useActiveLearningConfiguration(projectIdentifier, project.tasks);

    const isLoadingData = isPending || isLoadingModels;

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
    const { autoTrainingTasks, isPending } = useActiveLearningConfiguration(projectIdentifier, project.tasks);

    const filteredTaskAutoTraining = autoTrainingTasks.filter(({ task }) => task.id === selectedTask?.id);
    const filteredAutoTrainingTask = isNil(selectedTask) ? autoTrainingTasks : filteredTaskAutoTraining;

    return (
        <DialogTrigger type='popover' hideArrow>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    width={15}
                    isDisabled={isPending}
                    id={'active-learning-configuration-button'}
                    aria-label={'Active learning configuration'}
                    colorVariant={isDarkMode ? 'dark' : 'light'}
                    zIndex={1}
                >
                    <AutoTraining width={15} aria-label={'tasks in progress'} />
                    {!isPending && (
                        <CornerIndicator
                            allAutoTrainingValues={filteredAutoTrainingTask.map((filteredTask) =>
                                Boolean(filteredTask.trainingConfig?.value)
                            )}
                        />
                    )}
                </ActionButton>

                <Tooltip>Active learning configuration</Tooltip>
            </TooltipTrigger>
            <ActiveLearningConfigurationDialog selectedTask={selectedTask} />
        </DialogTrigger>
    );
};
