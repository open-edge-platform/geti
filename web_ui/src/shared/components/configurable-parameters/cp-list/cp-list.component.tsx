// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@geti/ui';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../../animation-parameters/animation-parameters';
import { ConfigParameterItemProp, ConfigurableParametersParams } from '../configurable-parameters.interface';
import { CPParamItem } from '../cp-item/cp-item.component';
import { useCPRule } from '../use-rule.hook';

interface CPParamsListProps extends ConfigParameterItemProp {
    parameters: ConfigurableParametersParams[];
    header: string;
}

export const CPParamsList = ({ parameters, updateParameter, header }: CPParamsListProps): JSX.Element => {
    const resetParameter = (parameter: ConfigurableParametersParams) => {
        updateParameter && updateParameter(parameter.id, parameter.defaultValue);
    };

    const { isEnablementRule, areEnabledFieldsFromRule, ruleImpactedFields } = useCPRule(
        header,
        parameters,
        resetParameter
    );

    return (
        <View>
            <AnimatePresence>
                {parameters.map((parameter, index) => {
                    const shouldFieldBeHidden =
                        isEnablementRule && ruleImpactedFields.includes(parameter.name) && !areEnabledFieldsFromRule;

                    return (
                        <motion.div
                            variants={ANIMATION_PARAMETERS.ANIMATE_LIST}
                            initial={'hidden'}
                            animate={'visible'}
                            exit={'hidden'}
                            layoutId={parameter.id}
                            custom={index}
                            key={parameter.id}
                        >
                            {shouldFieldBeHidden ? (
                                <></>
                            ) : (
                                <CPParamItem parameter={parameter} updateParameter={updateParameter} />
                            )}
                        </motion.div>
                    );
                })}
            </AnimatePresence>
        </View>
    );
};
