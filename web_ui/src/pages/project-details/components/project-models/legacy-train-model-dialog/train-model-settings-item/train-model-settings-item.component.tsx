// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
