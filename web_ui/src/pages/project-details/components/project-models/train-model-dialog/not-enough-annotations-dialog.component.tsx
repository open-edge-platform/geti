// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, FC } from 'react';

import { useNavigateToAnnotatorRoute } from '@geti/core/src/services/use-navigate-to-annotator-route.hook';
import { Button, ButtonGroup, Content, Dialog, dimensionValue, Divider, Flex, Heading, Text } from '@geti/ui';

import { isAnomalyDomain } from '../../../../../core/projects/domains';
import { Task } from '../../../../../core/projects/task.interface';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { NotEnoughWarning } from '../../common/not-enough-warning/not-enough-warning.component';
import { TaskSelection } from './model-types/task-selection.component';

interface NotEnoughAnnotationsDialogProps {
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
    onClose,
    tasks,
    selectedTask,
    onTaskChange,
    numberOfRequiredAnnotations,
}) => {
    const { projectIdentifier, isTaskChainProject, isSingleDomainProject, project } = useProject();
    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);
    const navigateToAnnotatorRoute = useNavigateToAnnotatorRoute();

    const handleGoToAnnotator = () => {
        const selectedDataset = project.datasets[0];
        navigateToAnnotatorRoute({
            datasetIdentifier: { ...projectIdentifier, datasetId: selectedDataset.id },
            active: selectedDataset.useForTraining && !isAnomalyProject,
        });
    };

    return (
        <Dialog maxWidth={'100rem'} width={'80vw'} UNSAFE_style={dialogStyles}>
            <Heading>Not enough annotations</Heading>
            <Divider size={'S'} />
            <Content>
                <Flex gap={'size-200'} direction={'column'}>
                    {isTaskChainProject && (
                        <TaskSelection tasks={tasks} onTaskChange={onTaskChange} selectedTask={selectedTask} />
                    )}

                    <NotEnoughWarning>
                        <Text>
                            Required number of annotations for this training:{' '}
                            <Text UNSAFE_style={{ fontWeight: 700 }}>{numberOfRequiredAnnotations}</Text>
                        </Text>
                    </NotEnoughWarning>
                    <Text UNSAFE_style={{ fontStyle: dimensionValue('size-200') }}>
                        You have not annotated enough media to train a model for {`"${selectedTask.title}" `}
                        task.
                        <br />
                        Please annotate more media to train a model.
                    </Text>
                </Flex>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose} id={'cancel-button-id'}>
                    Cancel
                </Button>

                <Button variant={'accent'} onPress={handleGoToAnnotator}>
                    {isAnomalyProject ? 'Explore' : 'Annotate interactively'}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
