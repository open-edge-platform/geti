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

import { ConfigurableParametersParams } from '../configurable-parameters.interface';
import { getStaticContent } from './utils';

describe('getStaticContent', () => {
    it('boolean', () => {
        expect(getStaticContent({ dataType: 'boolean', value: true } as ConfigurableParametersParams)).toEqual('On');
        expect(getStaticContent({ dataType: 'boolean', value: false } as ConfigurableParametersParams)).toEqual('Off');
    });
    it('integer', () => {
        expect(
            getStaticContent({ dataType: 'integer', value: undefined } as unknown as ConfigurableParametersParams)
        ).toEqual('');
    });
    it('float', () => {
        expect(getStaticContent({ dataType: 'float', value: 1.2 } as ConfigurableParametersParams)).toEqual(1.2);
        expect(
            getStaticContent({ dataType: 'float', value: undefined } as unknown as ConfigurableParametersParams)
        ).toEqual('');
    });
    it('string', () => {
        expect(getStaticContent({ dataType: 'string', value: 'test' } as ConfigurableParametersParams)).toEqual('test');
        expect(
            getStaticContent({ dataType: 'string', value: undefined } as unknown as ConfigurableParametersParams)
        ).toEqual('');
    });
});
