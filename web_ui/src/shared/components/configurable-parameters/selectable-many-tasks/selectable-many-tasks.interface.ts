// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersMany } from '../../../../core/configurable-parameters/services/configurable-parameters.interface';

export interface SelectableManyTasksProps extends Omit<ConfigurableParametersMany, 'type' | 'configParametersData'> {
    configurableParameters: ConfigurableParametersMany['configParametersData'];
}
