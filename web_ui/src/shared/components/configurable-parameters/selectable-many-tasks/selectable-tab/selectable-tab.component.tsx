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

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { ActionElement } from '../../../action-element/action-element.component';
import { ConfigurableParametersComponents, ConfigurableParametersMany } from '../../configurable-parameters.interface';

import classes from '../../selectable-customized-tabs/selectable-customized-tabs.module.scss';

interface SelectableTabProps extends Pick<ConfigurableParametersMany, 'setSelectedComponentId'> {
    isSelected: boolean;
    component: ConfigurableParametersComponents;
}

export const SelectableTab = ({ component, isSelected, setSelectedComponentId }: SelectableTabProps): JSX.Element => {
    // TODO: remove this after backend capitalises the strings on the server side
    const capitalizedHeader = component.header
        .split(' ')
        .map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
        .join(' ');

    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionElement
                UNSAFE_className={[classes.tabItem, isSelected ? classes.tabItemSelected : ''].join(' ')}
                onPress={() => setSelectedComponentId(component.id)}
            >
                {capitalizedHeader}
            </ActionElement>
            <Tooltip>{component.description}</Tooltip>
        </TooltipTrigger>
    );
};
