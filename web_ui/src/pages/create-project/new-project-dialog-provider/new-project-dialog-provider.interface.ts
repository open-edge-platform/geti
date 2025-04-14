// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../../../core/projects/core.interface';
import { TaskMetadata } from '../../../core/projects/task.interface';

export interface NewProjectDialogContextProps {
    metadata: ProjectMetadata;
    updateProjectState: (projectState: Partial<ProjectMetadata>) => void;
    hasNextStep: boolean;
    hasPreviousStep: boolean;
    goToNextStep: (() => void | null) | undefined;
    goToPreviousStep: (() => void | null) | undefined;
    resetSteps: () => void;
    content: JSX.Element;
    validationError?: { tree: string | undefined; labels: boolean; keypoint: string | undefined };
}

export type SingleTaskTemplateType = 'Detection' | 'Segmentation' | 'Classification' | 'Anomaly' | 'Keypoint Detection';
type TaskChainTemplateType = 'Chained tasks';

export type CreateNewProjectSelectedTabType = SingleTaskTemplateType | TaskChainTemplateType;

interface SelectProjectTemplateProps {
    name: string;
    selectedDomains: DOMAIN[];
    selectedTab: CreateNewProjectSelectedTabType;
    projectType: ProjectType;
    currentStep: STEPS;
}

interface ProjectLabelsManagementProps {
    projectTypeMetadata: TaskMetadata[];
}

export type ProjectMetadata = SelectProjectTemplateProps & ProjectLabelsManagementProps;

export interface StepInterface {
    component: JSX.Element;
    next: STEPS | null;
    previous: STEPS | null;
    key: STEPS;
}

export enum ProjectType {
    SINGLE = 'Single',
    TASK_CHAIN = 'Task chain',
}

export enum STEPS {
    NAME_PROJECT = 'name-project',
    SELECT_TEMPLATE = 'select-template',
    LABEL_MANAGEMENT = 'label-management',
    LABEL_MANAGEMENT_SECOND_TASK = 'label-management-second-task',
    POSE_TEMPLATE = 'pose-template',
}
