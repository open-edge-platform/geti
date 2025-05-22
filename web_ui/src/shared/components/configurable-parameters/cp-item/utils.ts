// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersParams } from '../../../../core/configurable-parameters/services/configurable-parameters.interface';

export const getStaticContent = (parameter: ConfigurableParametersParams): string | number => {
    let content: string | number = '';
    if (parameter.dataType === 'boolean') {
        content = parameter.value ? 'On' : 'Off';
    } else if (
        (parameter.dataType === 'integer' || parameter.dataType === 'float' || parameter.dataType === 'string') &&
        parameter.value !== undefined
    ) {
        content = parameter.value;
    }
    return content;
};
