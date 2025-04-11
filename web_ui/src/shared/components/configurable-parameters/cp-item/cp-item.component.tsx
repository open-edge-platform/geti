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

import { Divider, Flex, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { Alert } from '../../../../assets/icons';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { ActionElement } from '../../action-element/action-element.component';
import { InfoTooltip } from '../../info-tooltip/info-tooltip.component';
import { ConfigParameterItemProp, ConfigurableParametersParams } from '../configurable-parameters.interface';
import { CPEditableItem } from './cp-editable-item/cp-editable-item.component';
import { CPStaticItem } from './cp-static-item/cp-static-item.component';
import { ResetButton } from './reset-button/reset-button.component';
import { getStaticContent } from './utils';

import classes from './cp-item.module.scss';

interface CPParamItemProps extends ConfigParameterItemProp {
    parameter: ConfigurableParametersParams;
}

export const CPParamItem = ({ parameter, updateParameter }: CPParamItemProps): JSX.Element => {
    const { header, description, warning, editable } = parameter;
    const headerId = `${idMatchingFormat(header)}`;
    const isReadOnly = !editable;

    const handleResetButton = () => {
        updateParameter && updateParameter(parameter.id, parameter.defaultValue);
    };

    return (
        <View marginBottom={'size-65'}>
            <Flex justifyContent={'space-between'} alignItems={'center'}>
                <Flex width={'100%'}>
                    <Text id={`${headerId}-id`} UNSAFE_className={classes.configParameterTitle}>
                        {header}
                    </Text>
                </Flex>
                <Flex alignItems={'center'} gap={'size-100'}>
                    {warning && !isReadOnly ? (
                        <TooltipTrigger placement={'bottom'}>
                            <ActionElement
                                width={16}
                                height={16}
                                id={`${headerId}-warning-id`}
                                UNSAFE_className={classes.configParameterTooltipButton}
                            >
                                <Alert aria-label='Notification Alert' color='notice' />
                            </ActionElement>
                            <Tooltip>{warning}</Tooltip>
                        </TooltipTrigger>
                    ) : (
                        <></>
                    )}
                    <InfoTooltip id={`${headerId}-tooltip-id`} tooltipText={description} />

                    {!isReadOnly ? (
                        <>
                            <ResetButton
                                id={`${headerId}-reset-button-id`}
                                handleResetButton={handleResetButton}
                                isDisabled={parameter.value === parameter.defaultValue}
                            />
                        </>
                    ) : (
                        <></>
                    )}
                </Flex>
            </Flex>
            <View marginTop={'size-125'} marginBottom={'size-225'} UNSAFE_className={classes.configParameterContent}>
                {!isReadOnly && updateParameter ? (
                    <CPEditableItem updateParameter={updateParameter} parameter={parameter} id={headerId} />
                ) : (
                    <CPStaticItem id={`${headerId}-content-id`} content={getStaticContent(parameter)} />
                )}
            </View>
            <Divider size={'S'} UNSAFE_className={classes.configParameterDivider} />
        </View>
    );
};
