// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, Key, SetStateAction } from 'react';

import { Flex, Item, Picker, PressableElement, Text, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { Heading } from '@react-spectrum/text';
import { capitalize, isEmpty } from 'lodash-es';

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
                                    <PressableElement
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
                                    </PressableElement>
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
