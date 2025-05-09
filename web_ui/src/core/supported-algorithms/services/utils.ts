// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { capitalize } from 'lodash-es';

import { DOMAIN } from '../../projects/core.interface';
import { getDomain } from '../../projects/project.interface';
import {
    PerformanceCategory,
    SupportedAlgorithmDTO,
    SupportedAlgorithmsResponseDTO,
} from '../dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../supported-algorithms.interface';

const getSupportedAlgorithmEntity = (supportedAlgorithm: SupportedAlgorithmDTO): SupportedAlgorithm => {
    const {
        task_type,
        model_template_id,
        model_size,
        name,
        gigaflops,
        summary,
        default_algorithm,
        performance_category,
        lifecycle_stage,
    } = supportedAlgorithm;
    const domain = getDomain(task_type) as DOMAIN;

    return {
        domain,
        summary,
        gigaflops,
        name,
        modelSize: model_size,
        templateName: performance_category !== PerformanceCategory.OTHER ? capitalize(performance_category) : undefined,
        isDefaultAlgorithm: default_algorithm,
        modelTemplateId: model_template_id,
        lifecycleStage: lifecycle_stage,
        performanceCategory: performance_category,
        license: 'Apache 2.0',
    };
};

export const getSupportedAlgorithmsEntities = ({
    supported_algorithms,
}: SupportedAlgorithmsResponseDTO): SupportedAlgorithm[] => supported_algorithms.map(getSupportedAlgorithmEntity);
