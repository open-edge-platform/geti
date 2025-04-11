// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ConfigurableParametersParams, EntityIdentifier } from './configurable-parameters.interface';
import { getNewParameterValue, isLearningParametersTab } from './utils';

describe('configurable-parameters utils', () => {
    it('isLearningParametersTab', () => {
        expect(
            isLearningParametersTab({
                type: 'COMPONENT_PARAMETERS',
                groupName: 'learning_parameters',
            } as unknown as EntityIdentifier)
        ).toEqual(false);

        expect(
            isLearningParametersTab({
                type: 'HYPER_PARAMETER_GROUP',
                groupName: 'learning_parameters',
            } as unknown as EntityIdentifier)
        ).toEqual(true);
    });

    it('getNewParameterValue', () => {
        expect(getNewParameterValue({ dataType: 'boolean' } as unknown as ConfigurableParametersParams, false)).toEqual(
            { dataType: 'boolean', value: false }
        );
        expect(getNewParameterValue({ dataType: 'string' } as unknown as ConfigurableParametersParams, 'test')).toEqual(
            { dataType: 'string', value: 'test' }
        );
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
});
