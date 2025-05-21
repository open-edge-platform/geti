// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersParams } from '../../../core/configurable-parameters/services/configurable-parameters.interface';
import { usePrevious } from '../../../hooks/use-previous/use-previous.hook';
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
