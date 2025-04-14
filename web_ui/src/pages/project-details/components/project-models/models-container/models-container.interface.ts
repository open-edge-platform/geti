// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ModelGroupsAlgorithmDetails } from '../../../../../core/models/models.interface';

export type ModelContainerProps = Omit<ModelGroupsAlgorithmDetails, 'name' | 'modelTemplateName'>;
