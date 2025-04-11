// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
