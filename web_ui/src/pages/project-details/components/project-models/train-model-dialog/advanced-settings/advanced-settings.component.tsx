// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { Flex, Item, TabList, TabPanels, Tabs, Text, View } from '@adobe/react-spectrum';

import { Task } from '../../../../../../core/projects/task.interface';
import { SupportedAlgorithm } from '../../../../../../core/supported-algorithms/supported-algorithms.interface';
import { ConfigurableParametersTaskChain } from '../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { TaskSelection } from '../model-types/task-selection.component';
import { DataManagement } from './data-management/data-management.component';
import { ModelArchitectures } from './model-architectures/model-architectures.component';
import { Training } from './training/training.component';

const ContentWrapper: FC<{ children: ReactNode }> = ({ children }) => {
    return (
        <View padding={'size-250'} backgroundColor={'gray-50'}>
            {children}
        </View>
    );
};

interface AdvancedSettingsProps {
    tasks: Task[];
    selectedTask: Task;
    onTaskChange: (task: Task) => void;
    isTaskChainProject: boolean;
    algorithms: SupportedAlgorithm[];
    selectedModelTemplateId: string | null;
    onChangeSelectedTemplateId: (modelTemplateId: string | null) => void;
    activeModelTemplateId: string | null;
    isReshufflingSubsetsEnabled: boolean;
    onReshufflingSubsetsEnabledChange: (reshufflingSubsetsEnabled: boolean) => void;
    configParameters: ConfigurableParametersTaskChain;
    trainFromScratch: boolean;
    onTrainFromScratchChange: (trainFromScratch: boolean) => void;
}

interface TabProps {
    name: string;
    children: ReactNode;
}

export const AdvancedSettings: FC<AdvancedSettingsProps> = ({
    configParameters,
    tasks,
    selectedTask,
    onTaskChange,
    isTaskChainProject,
    algorithms,
    selectedModelTemplateId,
    onChangeSelectedTemplateId,
    activeModelTemplateId,
    isReshufflingSubsetsEnabled,
    onReshufflingSubsetsEnabledChange,
    trainFromScratch,
    onTrainFromScratchChange,
}) => {
    const TABS: TabProps[] = [
        {
            name: 'Architecture',
            children: (
                <ModelArchitectures
                    algorithms={algorithms}
                    selectedModelTemplateId={selectedModelTemplateId}
                    activeModelTemplateId={activeModelTemplateId}
                    onChangeSelectedTemplateId={onChangeSelectedTemplateId}
                />
            ),
        },
        {
            name: 'Data management',
            children: (
                <DataManagement
                    configParameters={configParameters}
                    isReshufflingSubsetsEnabled={isReshufflingSubsetsEnabled}
                    onReshufflingSubsetsEnabledChange={onReshufflingSubsetsEnabledChange}
                />
            ),
        },
        {
            name: 'Training',
            children: (
                <Training
                    trainFromScratch={trainFromScratch}
                    onTrainFromScratchChange={onTrainFromScratchChange}
                    configParameters={configParameters}
                />
            ),
        },
        {
            name: 'Evaluation',
            children: <></>,
        },
    ];

    return (
        <Flex direction={'column'} gap={'size-100'}>
            {isTaskChainProject && (
                <TaskSelection tasks={tasks} onTaskChange={onTaskChange} selectedTask={selectedTask} />
            )}
            <Tabs items={TABS}>
                <TabList>
                    {(tab: TabProps) => (
                        <Item key={tab.name} textValue={tab.name}>
                            <Text>{tab.name}</Text>
                        </Item>
                    )}
                </TabList>
                <TabPanels marginTop={'size-250'}>
                    {(tab: TabProps) => (
                        <Item key={tab.name} textValue={tab.name}>
                            <ContentWrapper>{tab.children}</ContentWrapper>
                        </Item>
                    )}
                </TabPanels>
            </Tabs>
        </Flex>
    );
};
