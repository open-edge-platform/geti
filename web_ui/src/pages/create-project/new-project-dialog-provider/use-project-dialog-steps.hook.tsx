// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { SetValidationProps, ValidationErrorType } from '../../../core/labels/label-tree-view.interface';
import { DOMAIN } from '../../../core/projects/core.interface';
import { isAnomalyDomain, isKeypointDetection } from '../../../core/projects/domains';
import { AnimationDirections } from '../../../shared/animation-parameters/animation-parameters';
import { NameProject } from '../components/name-project/name-project.component';
import { PoseTemplate } from '../components/pose-template/pose-template.component';
import { ProjectLabelsManagement } from '../components/project-labels-management/project-labels-management.component';
import { SelectProjectTemplate } from '../components/select-project-template/select-project-template.component';
import { ProjectMetadata, ProjectType, StepInterface, STEPS } from './new-project-dialog-provider.interface';

const PROJECT_CREATION_INITIAL_STATE: ProjectMetadata = {
    name: 'Project',
    selectedDomains: [],
    projectTypeMetadata: [],
    currentStep: STEPS.NAME_PROJECT,
    selectedTab: 'Detection',
    projectType: ProjectType.SINGLE,
};

interface UseProjectDialogSteps {
    projectCreationState: ProjectMetadata;
    updateProjectState: (projectState: Partial<ProjectMetadata>) => void;
    hasNextStep: boolean;
    hasPreviousStep: boolean;
    goToNextStep: () => void;
    goToPreviousStep: () => void;
    resetSteps: () => void;
    component: JSX.Element;
    validationError: { tree: string | undefined; labels: boolean; keypoint: string | undefined };
}

const getNextStep = (domain: DOMAIN) => {
    if (isAnomalyDomain(domain)) {
        return null;
    }

    if (isKeypointDetection(domain)) {
        return STEPS.POSE_TEMPLATE;
    }

    return STEPS.LABEL_MANAGEMENT;
};

export const useProjectDialogSteps = (): UseProjectDialogSteps => {
    const [animationDirection, setAnimationDirection] = useState<number>(AnimationDirections.MOVE_LEFT);
    const [projectCreationState, setProjectCreationState] = useState<ProjectMetadata>(PROJECT_CREATION_INITIAL_STATE);
    const [keypointError, setKeypointError] = useState<string | undefined>();
    const [treeValidationError, setTreeValidationError] = useState<string | undefined>();
    const [labelsValidationError, setLabelsValidationError] = useState<boolean>(false);

    const setValidationError = (options: SetValidationProps) => {
        if (options.type === ValidationErrorType.TREE) {
            setTreeValidationError(options.validationError);
        } else {
            setLabelsValidationError(options.validationError);
        }
    };

    const goToNextStep = () => {
        if (currentStep.next) {
            setAnimationDirection(() => AnimationDirections.MOVE_RIGHT);
            updateStep(currentStep.next);
        }
    };

    const getSteps = (key: STEPS, domains: DOMAIN[]): StepInterface => {
        const { projectType, projectTypeMetadata } = projectCreationState;

        const canCreateProject = projectType === ProjectType.SINGLE && projectTypeMetadata.length === 1;

        switch (key) {
            case STEPS.NAME_PROJECT:
                return {
                    component: (
                        <NameProject
                            metadata={projectCreationState}
                            updateProjectState={updateProjectState}
                            setValidationError={setTreeValidationError}
                            goToNextStep={goToNextStep}
                        />
                    ),
                    next: STEPS.SELECT_TEMPLATE,
                    previous: null,
                    key: STEPS.NAME_PROJECT,
                };
            case STEPS.SELECT_TEMPLATE:
                return {
                    component: (
                        <SelectProjectTemplate
                            metadata={projectCreationState}
                            updateProjectState={updateProjectState}
                            animationDirection={animationDirection}
                            setValidationError={setTreeValidationError}
                        />
                    ),
                    next: getNextStep(domains[0]),
                    previous: STEPS.NAME_PROJECT,
                    key: STEPS.SELECT_TEMPLATE,
                };
            case STEPS.LABEL_MANAGEMENT:
                return {
                    component: (
                        <ProjectLabelsManagement
                            updateProjectState={updateProjectState}
                            goToNextStep={goToNextStep}
                            metadata={projectCreationState}
                            validationError={treeValidationError}
                            animationDirection={animationDirection}
                            setValidationError={setValidationError}
                            selectedDomain={projectCreationState.selectedDomains[0]}
                        />
                    ),
                    next: canCreateProject ? null : STEPS.LABEL_MANAGEMENT_SECOND_TASK,
                    previous: STEPS.SELECT_TEMPLATE,
                    key: STEPS.LABEL_MANAGEMENT,
                };
            case STEPS.LABEL_MANAGEMENT_SECOND_TASK:
                return {
                    component: (
                        <ProjectLabelsManagement
                            updateProjectState={updateProjectState}
                            goToNextStep={goToNextStep}
                            metadata={projectCreationState}
                            validationError={treeValidationError}
                            animationDirection={animationDirection}
                            setValidationError={setValidationError}
                            selectedDomain={projectCreationState.selectedDomains[1]}
                            key={projectCreationState.selectedDomains[1]}
                        />
                    ),
                    next: null,
                    previous: STEPS.LABEL_MANAGEMENT,
                    key: STEPS.LABEL_MANAGEMENT_SECOND_TASK,
                };
            case STEPS.POSE_TEMPLATE:
                return {
                    component: (
                        <PoseTemplate
                            keypointError={keypointError}
                            animationDirection={animationDirection}
                            setValidationError={setKeypointError}
                            updateProjectState={updateProjectState}
                        />
                    ),
                    next: null,
                    previous: STEPS.SELECT_TEMPLATE,
                    key: STEPS.POSE_TEMPLATE,
                };
        }
    };

    const resetSteps = (): void => {
        setProjectCreationState(() => PROJECT_CREATION_INITIAL_STATE);
        setValidationError({ type: ValidationErrorType.TREE, validationError: undefined });
        setValidationError({ type: ValidationErrorType.LABELS, validationError: false });
    };

    const updateProjectState = (projectState: Partial<ProjectMetadata>) => {
        setProjectCreationState((prevState) => ({ ...prevState, ...projectState }));
    };

    const updateStep = (stepKey: STEPS): void => {
        setProjectCreationState((prevState) => ({ ...prevState, currentStep: stepKey }));
    };

    const currentStep = getSteps(projectCreationState.currentStep, projectCreationState.selectedDomains);

    const hasNextStep = currentStep.next !== null;

    const hasPreviousStep = currentStep.previous !== null;

    const goToPreviousStep = () => {
        if (currentStep.previous) {
            setAnimationDirection(() => AnimationDirections.MOVE_LEFT);
            updateStep(currentStep.previous);
        }
    };

    return {
        projectCreationState,
        updateProjectState,
        hasNextStep,
        hasPreviousStep,
        goToNextStep,
        goToPreviousStep,
        resetSteps,
        component: currentStep.component,
        validationError: { tree: treeValidationError, labels: labelsValidationError, keypoint: keypointError },
    };
};
