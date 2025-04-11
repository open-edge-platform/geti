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

import { CSSProperties, FC, Key } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Flex, Heading, Text } from '@adobe/react-spectrum';

import { isAnomalyDomain } from '../../../../../core/projects/domains';
import { Task } from '../../../../../core/projects/task.interface';
import { useNavigateToAnnotatorRoute } from '../../../../../core/services/use-navigate-to-annotator-route.hook';
import { Button } from '../../../../../shared/components/button/button.component';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { NotEnoughWarning } from '../../common/not-enough-warning/not-enough-warning.component';
import { TaskSelection } from './model-templates-selection/task-selection.component';

import classes from './train-model-dialog.module.scss';

interface NotEnoughAnnotationsDialogProps {
    isOpen: boolean;
    onClose: () => void;
    tasks: Task[];
    selectedTask: Task;
    onTaskChange: (task: Task) => void;
    numberOfRequiredAnnotations: number;
}

const dialogStyles = {
    '--spectrum-dialog-padding-x': 'var(--spectrum-global-dimension-size-250)',
    '--spectrum-dialog-padding-y': 'var(--spectrum-global-dimension-size-350)',
} as CSSProperties;

export const NotEnoughAnnotationsDialog: FC<NotEnoughAnnotationsDialogProps> = ({
    isOpen,
    onClose,
    tasks,
    selectedTask,
    onTaskChange,
    numberOfRequiredAnnotations,
}) => {
    const { projectIdentifier, isTaskChainProject, isSingleDomainProject, project } = useProject();
    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);
    const navigateToAnnotatorRoute = useNavigateToAnnotatorRoute(projectIdentifier);

    const handleGoToAnnotator = () => {
        const selectedDataset = project.datasets[0];
        navigateToAnnotatorRoute({
            datasetId: selectedDataset.id,
            active: selectedDataset.useForTraining && !isAnomalyProject,
        });
    };

    const handleChangeTask = (domain: Key) => {
        const newSelectedTask = tasks.find((task) => task.domain === domain);

        if (newSelectedTask === undefined || newSelectedTask.id === selectedTask.id) {
            return;
        }

        onTaskChange(newSelectedTask);
    };

    return (
        <DialogContainer onDismiss={onClose}>
            {isOpen && (
                <Dialog maxWidth={'100rem'} width={'80vw'} UNSAFE_style={dialogStyles}>
                    <Heading>Not enough annotations</Heading>
                    <Divider size={'S'} />
                    <Content>
                        <Flex gap={'size-200'} direction={'column'}>
                            {isTaskChainProject && (
                                <TaskSelection
                                    tasks={tasks}
                                    onTaskChange={handleChangeTask}
                                    selectedTask={selectedTask.domain}
                                />
                            )}

                            <NotEnoughWarning>
                                <Text>
                                    Required number of annotations for this training:{' '}
                                    <Text UNSAFE_style={{ fontWeight: 700 }}>{numberOfRequiredAnnotations}</Text>
                                </Text>
                            </NotEnoughWarning>
                            <Text UNSAFE_className={classes.notEnoughAnnotations}>
                                You have not annotated enough media to train a model for {`"${selectedTask.title}" `}
                                task.
                                <br />
                                Please annotate more media to train a model.
                            </Text>
                        </Flex>
                    </Content>
                    <ButtonGroup UNSAFE_className={classes.buttonGroup}>
                        <Button variant={'secondary'} onPress={onClose} id={'cancel-button-id'}>
                            Cancel
                        </Button>

                        <Button variant={'accent'} onPress={handleGoToAnnotator}>
                            {isAnomalyProject ? 'Explore' : 'Annotate interactively'}
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
