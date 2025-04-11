// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { View } from '@adobe/react-spectrum';
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
