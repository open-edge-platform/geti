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

import { useState } from 'react';

import { Flex, Text, View } from '@adobe/react-spectrum';

import { ChevronRightSmallLight, ChevronUpLight } from '../../../../assets/icons';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { ActionButton } from '../../button/button.component';
import { ConfigParameterItemProp, ConfigurableParametersGroups } from '../configurable-parameters.interface';
import { CPParamsList } from '../cp-list/cp-list.component';

import classes from './cp-group-item.module.scss';

interface CPGroupItemProps extends ConfigParameterItemProp {
    group: ConfigurableParametersGroups;
    isExpandable: boolean;
}

export const CPGroupItem = ({ group, isExpandable, updateParameter }: CPGroupItemProps): JSX.Element => {
    const { header, parameters } = group;

    const [isExpanded, setIsExpanded] = useState<boolean>(false);

    return (
        <View marginBottom={'size-125'} marginEnd={'size-150'}>
            <Flex alignItems={'center'} justifyContent={'space-between'} marginBottom={'size-75'}>
                <Text id={`${idMatchingFormat(header)}-id`} UNSAFE_className={classes.configGroupHeaderTitle}>
                    {header}
                </Text>
                {isExpandable ? (
                    <ActionButton
                        id={`${idMatchingFormat(header)}-expand-button-id`}
                        isQuiet
                        onPress={() => setIsExpanded(!isExpanded)}
                        aria-label={'Show and hide group'}
                    >
                        {isExpanded ? (
                            <ChevronUpLight id={'chevron-up-id'} />
                        ) : (
                            <ChevronRightSmallLight id={'chevron-down-id'} />
                        )}
                    </ActionButton>
                ) : (
                    <></>
                )}
            </Flex>
            {isExpandable ? (
                isExpanded ? (
                    <CPParamsList parameters={parameters} updateParameter={updateParameter} header={header} />
                ) : (
                    <></>
                )
            ) : (
                <CPParamsList parameters={parameters} updateParameter={updateParameter} header={header} />
            )}
        </View>
    );
};
