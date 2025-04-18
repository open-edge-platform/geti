// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useEffect } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

import { useConfigParameters } from '../../../../../../core/configurable-parameters/hooks/use-config-parameters.hook';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';
import { ConfigParamsPlaceholder } from '../../../../../../shared/components/configurable-parameters/config-params-placeholder/config-params-placeholder.component';
import { ConfigurableParameters } from '../../../../../../shared/components/configurable-parameters/configurable-parameters.component';
import {
    ConfigurableParametersSingle,
    ConfigurableParametersTaskChain,
    ConfigurableParametersType,
} from '../../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { SliderAnimation } from '../../../../../../shared/components/slider-animation/slider-animation.component';
import { TrainModelSettingsItem } from '../train-model-settings-item/train-model-settings-item.component';
import { RESHUFFLE_SUBSETS_TOOLTIP_MSG, TRAIN_FROM_SCRATCH_TOOLTIP_MSG } from '../utils';

interface TrainConfigurableParametersProps {
    modelTemplateId: string;
    taskId: string;
    configParameters: ConfigurableParametersTaskChain | undefined;
    setConfigParameters: Dispatch<SetStateAction<ConfigurableParametersTaskChain | undefined>>;
    updateParameter: ConfigurableParametersSingle['updateParameter'];
    trainFromScratch: boolean;
    setTrainFromScratch: (trainFromScratch: boolean) => void;
    animationDirection: number;
    isReshufflingSubsetsEnabled: boolean;
    onChangeReshuffleSubsets: (isReshufflingSubsetsEnabled: boolean) => void;
}

export const TrainConfigurableParameters = ({
    modelTemplateId,
    taskId,
    configParameters,
    setConfigParameters,
    trainFromScratch,
    setTrainFromScratch,
    updateParameter,
    animationDirection,
    isReshufflingSubsetsEnabled,
    onChangeReshuffleSubsets,
}: TrainConfigurableParametersProps): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { useGetModelConfigParameters } = useConfigParameters(projectIdentifier);
    const { isLoading, data: configParametersData } = useGetModelConfigParameters(
        taskId,
        undefined,
        modelTemplateId,
        true
    );

    useEffect(() => {
        // update state only when configParameters are undefined
        if (configParametersData && !configParameters) {
            setConfigParameters(configParametersData);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [configParametersData]);

    return (
        <Flex direction='column' height='100%' UNSAFE_style={{ marginTop: 0 }}>
            <View
                backgroundColor='gray-50'
                borderColor='gray-50'
                borderRadius='regular'
                padding={{ base: 'size-150', L: 'size-250' }}
                paddingEnd={0}
                UNSAFE_style={{ boxSizing: 'border-box', overflow: 'hidden' }}
                flex={1}
            >
                {isLoading ? (
                    <SliderAnimation animationDirection={animationDirection} style={{ height: '100%' }}>
                        <ConfigParamsPlaceholder />
                    </SliderAnimation>
                ) : (
                    configParameters && (
                        <SliderAnimation animationDirection={animationDirection} style={{ height: '100%' }}>
                            <ConfigurableParameters
                                type={ConfigurableParametersType.SINGLE_CONFIG_PARAMETERS}
                                configParametersData={configParameters}
                                updateParameter={updateParameter}
                            />
                        </SliderAnimation>
                    )
                )}
            </View>

            {!isLoading && configParameters && (
                <SliderAnimation animationDirection={animationDirection}>
                    <View marginTop={'size-200'} marginStart={'size-150'}>
                        <TrainModelSettingsItem
                            text={'Train from scratch'}
                            tooltip={TRAIN_FROM_SCRATCH_TOOLTIP_MSG}
                            isSelected={trainFromScratch}
                            handleIsSelected={setTrainFromScratch}
                        />
                    </View>
                    <View marginStart={'size-350'}>
                        <TrainModelSettingsItem
                            text={'Reshuffle subsets'}
                            tooltip={RESHUFFLE_SUBSETS_TOOLTIP_MSG}
                            isDisabled={!trainFromScratch}
                            isSelected={isReshufflingSubsetsEnabled}
                            handleIsSelected={onChangeReshuffleSubsets}
                        />
                    </View>
                </SliderAnimation>
            )}
        </Flex>
    );
};
