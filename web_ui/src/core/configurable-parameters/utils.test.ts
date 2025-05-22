// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersParams } from './services/configurable-parameters.interface';
import { getNewParameterValue } from './utils';

it('getNewParameterValue', () => {
    expect(getNewParameterValue({ dataType: 'boolean' } as unknown as ConfigurableParametersParams, false)).toEqual({
        dataType: 'boolean',
        value: false,
    });
    expect(getNewParameterValue({ dataType: 'string' } as unknown as ConfigurableParametersParams, 'test')).toEqual({
        dataType: 'string',
        value: 'test',
    });
    expect(getNewParameterValue({ dataType: 'integer' } as unknown as ConfigurableParametersParams, 1)).toEqual({
        dataType: 'integer',
        value: 1,
    });
    expect(getNewParameterValue({ dataType: 'float' } as unknown as ConfigurableParametersParams, 1)).toEqual({
        dataType: 'float',
        value: 1,
    });
    expect(getNewParameterValue({ dataType: 'number' } as unknown as ConfigurableParametersParams, 1)).toEqual({
        dataType: 'number',
    });
});
