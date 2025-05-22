// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersParams } from '../../../../core/configurable-parameters/services/configurable-parameters.interface';
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
