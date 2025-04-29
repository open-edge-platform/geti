// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ProjectIdentifier } from '../../projects/core.interface';
import { SupportedAlgorithm } from '../supported-algorithms.interface';

export interface SupportedAlgorithmsService {
    getProjectSupportedAlgorithms: (projectIdentifier: ProjectIdentifier) => Promise<SupportedAlgorithm[]>;
}
