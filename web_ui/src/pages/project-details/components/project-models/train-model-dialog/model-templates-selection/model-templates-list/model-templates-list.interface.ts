// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    LifecycleStage,
    PerformanceCategory,
} from '../../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import {
    ModelTemplatesNames,
    SupportedAlgorithm,
} from '../../../../../../../core/supported-algorithms/supported-algorithms.interface';

export interface Template {
    text: ModelTemplatesNames;
    name: string;
    modelTemplateId: string;
    description: string;
    summary: string;
    isDefaultAlgorithm: boolean;
    performanceCategory: PerformanceCategory;
    lifecycleStage: LifecycleStage;
    gigaflops: number;
    modelSize: number;
}

export interface TrainModelTemplatesProps {
    templates: SupportedAlgorithm[];
    animationDirection: number;
    selectedDomain: string;

    activeModelTemplateIdPerTask: string | undefined;

    selectedModelTemplateId: string;
    handleSelectedTemplateId: (modelTemplateId: string | null) => void;
}

export const TEMPLATES: Template[] = [
    {
        text: ModelTemplatesNames.BALANCE,
        summary: '',
        gigaflops: 0,
        modelSize: 0,
        name: '',
        modelTemplateId: '',
        description: 'In balance with accuracy and speed.',
        isDefaultAlgorithm: false,
        lifecycleStage: LifecycleStage.ACTIVE,
        performanceCategory: PerformanceCategory.OTHER,
    },
    {
        text: ModelTemplatesNames.ACCURACY,
        summary: '',
        gigaflops: 0,
        modelSize: 0,
        name: '',
        modelTemplateId: '',
        description: 'More accurate, but slower.',
        isDefaultAlgorithm: false,
        lifecycleStage: LifecycleStage.ACTIVE,
        performanceCategory: PerformanceCategory.OTHER,
    },
    {
        text: ModelTemplatesNames.SPEED,
        summary: '',
        gigaflops: 0,
        modelSize: 0,
        name: '',
        modelTemplateId: '',
        description: 'Faster, but less accurate.',
        isDefaultAlgorithm: false,
        lifecycleStage: LifecycleStage.ACTIVE,
        performanceCategory: PerformanceCategory.OTHER,
    },
];
