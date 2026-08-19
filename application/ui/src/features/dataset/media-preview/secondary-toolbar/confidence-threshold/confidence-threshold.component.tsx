// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionButton, Flex, Text, View } from '@geti-ui/ui';
import { Refresh } from '@geti-ui/ui/icons';

import { NumberParameterField } from '../../../../../components/number-parameter-field/number-parameter-field.component';

import classes from './confidence-threshold.module.scss';

export const ConfidenceThreshold = ({ isDisabled }: { isDisabled: boolean }) => {
    return (
        <View>
            <Text UNSAFE_className={classes.label}>Confidence threshold</Text>
            <Flex width={'100%'} gap={'size-175'} alignItems={'center'}>
                <NumberParameterField
                    onChange={() => {}}
                    type={'float'}
                    name={'Confidence threshold'}
                    minValue={0}
                    maxValue={1}
                    step={0.001}
                    value={0.3}
                    isDisabled={isDisabled}
                />
                <ActionButton isQuiet onPress={() => {}} isDisabled={isDisabled}>
                    <Refresh />
                </ActionButton>
            </Flex>
        </View>
    );
};
