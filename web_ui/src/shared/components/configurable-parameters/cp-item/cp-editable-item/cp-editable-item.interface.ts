// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersParams, ConfigurableParametersSingle } from '../../configurable-parameters.interface';

export interface ResetButtonHandler extends Pick<ConfigurableParametersSingle, 'updateParameter'> {
    id: string;
}

export interface CPEditableItemProps extends ResetButtonHandler {
    parameter: ConfigurableParametersParams;
}
