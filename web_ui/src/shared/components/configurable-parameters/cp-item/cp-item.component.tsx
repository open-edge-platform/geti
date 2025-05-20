// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, PressableElement, Text, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { Alert } from '@geti/ui/icons';

import { idMatchingFormat } from '../../../../test-utils/id-utils';
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
                            <PressableElement
                                width={16}
                                height={16}
                                id={`${headerId}-warning-id`}
                                UNSAFE_className={classes.configParameterTooltipButton}
                            >
                                <Alert aria-label='Notification Alert' color='notice' />
                            </PressableElement>
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
