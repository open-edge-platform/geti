// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { DOMAIN } from '../../projects/core.interface';
import { TASK_TYPE } from '../../projects/dtos/task.interface';
import { LifecycleStage, PerformanceCategory, SupportedAlgorithmDTO } from '../dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../supported-algorithms.interface';
import { getSupportedAlgorithmsEntities } from './utils';

export const getMockedSupportedAlgorithm = (supportedAlgorithm?: Partial<SupportedAlgorithm>): SupportedAlgorithm => {
    const {
        name,
        summary,
        domain,
        templateName,
        modelTemplateId,
        modelSize,
        gigaflops,
        isDefaultAlgorithm,
        lifecycleStage,
        performanceCategory,
        license,
    } = supportedAlgorithm ?? {};

    return {
        name: name ?? 'Yolo algorithm',
        summary: summary ?? 'Description of the algorithm',
        domain: domain ?? DOMAIN.DETECTION,
        modelTemplateId: modelTemplateId ?? 'yolo-template-id',
        modelSize: modelSize ?? 1.2,
        gigaflops: gigaflops ?? 1.2,
        isDefaultAlgorithm: isDefaultAlgorithm ?? false,
        templateName,
        lifecycleStage: lifecycleStage || LifecycleStage.ACTIVE,
        performanceCategory: performanceCategory || PerformanceCategory.OTHER,
        license: license ?? 'Apache 2.0',
    };
};

export const mockedSupportedAlgorithmsDTO: SupportedAlgorithmDTO[] = [
    {
        name: 'Yolo',
        task_type: TASK_TYPE.DETECTION,
        model_size: 200,
        model_template_id: 'detection_yolo',
        gigaflops: 5,
        summary: 'YOLO architecture for detection',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
    {
        name: 'SSD',
        task_type: TASK_TYPE.DETECTION,
        model_size: 200,
        model_template_id: 'detection_ssd',
        gigaflops: 3,
        summary: 'SSD architecture for detection',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
    {
        name: 'HDD',
        task_type: TASK_TYPE.DETECTION,
        model_size: 300,
        model_template_id: 'detection_hdd',
        gigaflops: 1,
        summary: 'HDD architecture for detection',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
    {
        name: 'Efficient-B0',
        task_type: TASK_TYPE.CLASSIFICATION,
        model_size: 100,
        model_template_id: 'classification_efficient_b0',
        gigaflops: 0.8,
        summary: 'Efficient-B0 architecture for classification',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
    {
        name: 'Mobile-Net',
        task_type: TASK_TYPE.CLASSIFICATION,
        model_size: 300,
        model_template_id: 'classification_mobile_net',
        gigaflops: 1.1,
        summary: 'Mobile-Net architecture for classification',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
    {
        name: 'Segmentation-HDD',
        task_type: TASK_TYPE.SEGMENTATION,
        model_size: 250,
        model_template_id: 'segmentation_hdd',
        gigaflops: 1,
        summary: 'Segmentation-HDD architecture for segmentation',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
    {
        name: 'Anomaly-SSD',
        task_type: TASK_TYPE.ANOMALY_CLASSIFICATION,
        model_size: 300,
        model_template_id: 'anomaly_ssd',
        gigaflops: 1,
        summary: 'Anomaly-SSD architecture for anomaly',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
    {
        name: 'Segmentation-SSD',
        task_type: TASK_TYPE.SEGMENTATION,
        model_size: 150,
        model_template_id: 'segmentation_ssd',
        gigaflops: 23,
        summary: 'Segmentation-SSD for segmentation',
        default_algorithm: false,
        lifecycle_stage: LifecycleStage.ACTIVE,
        performance_category: PerformanceCategory.OTHER,
    },
];

export const mockedSupportedAlgorithms: SupportedAlgorithm[] = getSupportedAlgorithmsEntities({
    supported_algorithms: mockedSupportedAlgorithmsDTO,
});

export const mockedDetectionSupportedAlgorithms = mockedSupportedAlgorithms.filter(
    ({ domain }) => domain === DOMAIN.DETECTION
);
