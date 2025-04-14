// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../projects/core.interface';
import { SupportedAlgorithmDTO } from './dtos/supported-algorithms.interface';

export enum ModelTemplatesNames {
    ACCURACY = 'Accuracy',
    SPEED = 'Speed',
    BALANCE = 'Balance',
}

export interface SupportedAlgorithm {
    name: SupportedAlgorithmDTO['name'];
    modelSize: SupportedAlgorithmDTO['model_size'];
    modelTemplateId: SupportedAlgorithmDTO['model_template_id'];
    templateName: ModelTemplatesNames | undefined;
    domain: DOMAIN;
    summary: string;
    gigaflops: number;
    isDefaultAlgorithm: boolean;
    lifecycleStage: SupportedAlgorithmDTO['lifecycle_stage'];
    performanceCategory: SupportedAlgorithmDTO['performance_category'];
    license: string;
}

export type TaskWithSupportedAlgorithms = Record<string, SupportedAlgorithm[]>;
