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

import { Dispatch, Key, SetStateAction } from 'react';

import { Flex, Item, Picker, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import capitalize from 'lodash/capitalize';
import isEmpty from 'lodash/isEmpty';

import { ActionElement } from '../../../../../../shared/components/action-element/action-element.component';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';
import { NEAR_MEAN_TOOLTIP_MSG } from '../utils';
import { DistributionLabels } from './objects-list.interface';

import classes from './objects-list.module.scss';

interface ObjectsListProps {
    labels: DistributionLabels[];
    objectSizes: { name: string; color: string }[];
    selectedLabelKey: string;
    setSelectedLabelKey: Dispatch<SetStateAction<string>>;
}

export const ObjectsList = ({
    labels,
    objectSizes,
    selectedLabelKey,
    setSelectedLabelKey,
}: ObjectsListProps): JSX.Element => {
    const handleLabelChange = (label: Key): void => {
        setSelectedLabelKey(String(label));
    };

    return (
        <Flex direction={'column'} height={'100%'}>
            <Flex direction={'column'} alignItems={'start'}>
                <Text marginBottom={'size-50'} UNSAFE_className={classes.classText}>
                    Class
                </Text>
                <Picker
                    aria-label={'Object class'}
                    items={labels}
                    selectedKey={selectedLabelKey}
                    onSelectionChange={handleLabelChange}
                    marginBottom={'size-50'}
                    width={'size-2000'}
                >
                    {(item) => <Item key={item.name}>{capitalize(item.name)}</Item>}
                </Picker>
                <View>
                    <Heading marginBottom={'size-50'}>Object size</Heading>
                    <Flex direction={'column'} gap={'size-100'}>
                        {objectSizes.map(({ name, color }) =>
                            !isEmpty(color) ? (
                                <Flex alignItems={'center'} columnGap={'size-75'} marginTop={'size-50'} key={name}>
                                    <View
                                        UNSAFE_className={classes.objectSize}
                                        UNSAFE_style={{ backgroundColor: color }}
                                    />
                                    {name}
                                </Flex>
                            ) : (
                                <TooltipTrigger placement={'bottom'} key={name}>
                                    <ActionElement
                                        UNSAFE_className={classes.objectSizeNearMean}
                                        id={`${idMatchingFormat(name)}-object-list-button`}
                                    >
                                        <Flex alignItems={'center'} columnGap={'size-75'} marginTop={'size-50'}>
                                            <View
                                                UNSAFE_className={classes.objectSizeDashed}
                                                UNSAFE_style={{
                                                    backgroundColor: 'transparent',
                                                    fontWeight: 'var(--spectrum-global-font-weight-thin)',
                                                }}
                                            />
                                            {name}
                                        </Flex>
                                    </ActionElement>
                                    <Tooltip>{NEAR_MEAN_TOOLTIP_MSG}</Tooltip>
                                </TooltipTrigger>
                            )
                        )}
                    </Flex>
                </View>
            </Flex>
        </Flex>
    );
};
