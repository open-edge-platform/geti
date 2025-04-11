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

import { usePrevious } from '../../../hooks/use-previous/use-previous.hook';
import { ConfigurableParametersParams } from './configurable-parameters.interface';
import { ACTION_TYPES, CP_RULES } from './rules';

export const useCPRule = (
    header: string | undefined,
    parameters: ConfigurableParametersParams[],
    resetParameter: (param: ConfigurableParametersParams) => void
) => {
    const rule = CP_RULES.find(({ groupTitle }) => groupTitle === header);
    const isEnablementRule = rule?.action === ACTION_TYPES.ENABLEMENT;
    const areEnabledFieldsFromRule = isEnablementRule
        ? parameters.find(({ name }) => rule?.switchFieldName === name)?.value
        : true;

    const previousEnablement = usePrevious(areEnabledFieldsFromRule);

    if (!!previousEnablement && !areEnabledFieldsFromRule) {
        const chosenParameters = parameters.filter(({ name }) => isEnablementRule && rule?.groupFields.includes(name));
        chosenParameters.forEach((value) => {
            resetParameter(value);
        });
    }

    return { isEnablementRule, areEnabledFieldsFromRule, ruleImpactedFields: rule?.groupFields ?? [] };
};
