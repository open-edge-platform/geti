// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { EntityIdentifier } from '../../../core/configurable-parameters/services/configurable-parameters.interface';
import { isLearningParametersTab } from './utils';

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
});
