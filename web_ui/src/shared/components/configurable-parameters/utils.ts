// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { EntityIdentifier } from '../../../core/configurable-parameters/services/configurable-parameters.interface';

export const isLearningParametersTab = (entityIdentifier: EntityIdentifier): boolean => {
    return entityIdentifier.type === 'HYPER_PARAMETER_GROUP' && entityIdentifier.groupName === 'learning_parameters';
};
