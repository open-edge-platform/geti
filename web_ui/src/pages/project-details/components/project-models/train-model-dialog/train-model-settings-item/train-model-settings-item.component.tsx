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

import { FC } from 'react';

import { Flex } from '@adobe/react-spectrum';

import { Checkbox } from '../../../../../../shared/components/checkbox/checkbox.component';
import { InfoTooltip } from '../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './train-model-settings-item.module.scss';

interface TrainModelSettingsItemProps {
    text: string;
    tooltip: string;
    isSelected: boolean;
    isDisabled?: boolean;
    handleIsSelected: (isSelected: boolean) => void;
}

export const TrainModelSettingsItem: FC<TrainModelSettingsItemProps> = ({
    text,
    tooltip,
    isSelected,
    isDisabled = false,
    handleIsSelected,
}): JSX.Element => {
    return (
        <Flex gap={'size-100'} alignItems={'center'}>
            <Checkbox
                isSelected={isSelected}
                onChange={handleIsSelected}
                UNSAFE_className={classes.trainModelCheckbox}
                isDisabled={isDisabled}
            >
                {text}
            </Checkbox>
            <InfoTooltip id={`${idMatchingFormat(text)}-tooltip-id`} tooltipText={tooltip} />
        </Flex>
    );
};
