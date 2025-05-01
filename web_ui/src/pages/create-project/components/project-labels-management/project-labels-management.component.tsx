// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useMemo, useState } from 'react';

import { Divider } from '@adobe/react-spectrum';
import { SliderAnimation } from '@shared/components/slider-animation/slider-animation.component';
import { TutorialCardBuilder } from '@shared/components/tutorial-card/tutorial-card-builder.component';

import { LabelTreeItem, SetValidationProps } from '../../../../core/labels/label-tree-view.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { TUTORIAL_CARD_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { ProjectMetadata, STEPS } from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { DomainChainSteps } from './domain-chain-steps.component';
import { TaskLabelsManagement } from './task-labels-management/task-labels-management.component';
import { getLabelTreeType, getProjectLabels, getTutorialCardKey } from './utils';

interface ManageProjectLabelsProps {
    setValidationError: (options: SetValidationProps) => void;
    animationDirection: number;
    selectedDomain: DOMAIN;
    updateProjectState: (projectState: Partial<ProjectMetadata>) => void;
    metadata: ProjectMetadata;
    validationError: string | undefined;
    goToNextStep: (() => void | null) | undefined;
}

export const ProjectLabelsManagement = ({
    setValidationError,
    animationDirection,
    selectedDomain,
    updateProjectState,
    validationError,
    metadata,
    goToNextStep,
}: ManageProjectLabelsProps): JSX.Element => {
    const [selectedTask, setSelectedTask] = useState<DOMAIN>(selectedDomain);

    useEffect(() => {
        if (selectedDomain !== selectedTask) {
            setSelectedTask(selectedDomain);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedDomain]);

    const { projectTypeMetadata, selectedDomains: domains } = metadata;

    const isTaskChain = domains.length > 1;
    const projectLabels = getProjectLabels(projectTypeMetadata);
    const taskMetadata = projectTypeMetadata.find((task) => task.domain === selectedTask);

    const setTaskLabelsHandler = useCallback(
        (labels: LabelTreeItem[]) => {
            if (!taskMetadata) {
                return;
            }

            let updatedProjectInfo: TaskMetadata[];

            if (projectTypeMetadata.map((task) => task.domain).includes(selectedTask)) {
                updatedProjectInfo = projectTypeMetadata.map((task) => {
                    if (task.domain === selectedTask) {
                        return { ...task, labels };
                    } else {
                        return task;
                    }
                });
            } else {
                updatedProjectInfo = [
                    ...projectTypeMetadata,
                    { domain: selectedTask, labels, relation: taskMetadata.relation },
                ];
            }

            updateProjectState({ projectTypeMetadata: updatedProjectInfo });
        },
        [selectedTask, projectTypeMetadata, taskMetadata, updateProjectState]
    );

    const tutorialCardKey: TUTORIAL_CARD_KEYS | undefined = useMemo(() => {
        return taskMetadata ? getTutorialCardKey(selectedTask, isTaskChain, taskMetadata.relation) : undefined;
    }, [selectedTask, taskMetadata, isTaskChain]);

    if (!taskMetadata) {
        // In normal case taskMetadata should always be found on the list
        return <></>;
    }

    const handleNext = () => {
        !validationError && goToNextStep && goToNextStep();
    };

    return (
        <SliderAnimation
            animationDirection={animationDirection}
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        >
            {tutorialCardKey && <TutorialCardBuilder cardKey={tutorialCardKey} />}

            {isTaskChain ? (
                <>
                    <DomainChainSteps
                        domains={domains}
                        selected={selectedTask}
                        isValid={!validationError}
                        handleSelection={(domain: DOMAIN) => {
                            const step =
                                domain === domains[0] ? STEPS.LABEL_MANAGEMENT : STEPS.LABEL_MANAGEMENT_SECOND_TASK;

                            setSelectedTask(domain);
                            updateProjectState({ currentStep: step });
                        }}
                    />
                    <Divider size={'S'} />
                </>
            ) : (
                <></>
            )}

            <TaskLabelsManagement
                setValidationError={setValidationError}
                next={handleNext}
                type={getLabelTreeType(selectedTask, isTaskChain && selectedTask === domains[0])}
                setLabels={setTaskLabelsHandler}
                projectLabels={projectLabels}
                key={selectedDomain}
                taskMetadata={taskMetadata}
                domains={domains}
            />
        </SliderAnimation>
    );
};
