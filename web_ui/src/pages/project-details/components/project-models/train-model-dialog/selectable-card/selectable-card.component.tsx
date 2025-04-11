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

import { ReactNode } from 'react';

import { DimensionValue, Flex, View } from '@adobe/react-spectrum';
import { Responsive } from '@react-types/shared';
import { usePress } from 'react-aria';

import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

import classes from './selectable-card.module.scss';

interface SelectableCardProps {
    text: string;
    className?: string;
    isSelected: boolean;
    headerContent: ReactNode;
    descriptionContent: ReactNode;
    minHeight?: Responsive<DimensionValue> | undefined;
    handleOnPress: () => void;
}

export const SelectableCard = ({
    text,
    minHeight,
    className = '',
    isSelected,
    headerContent,
    descriptionContent,
    handleOnPress,
}: SelectableCardProps): JSX.Element => {
    const { pressProps } = usePress({
        onPress: () => {
            handleOnPress();
        },
    });

    return (
        <div
            {...pressProps}
            id={`${idMatchingFormat(text)}-id`}
            data-testid={`${idMatchingFormat(text)}-id`}
            aria-label={isSelected ? 'Selected card' : 'Not selected card'}
            className={[classes.selectableCard, isSelected ? classes.selectableCardSelected : '', className].join(' ')}
        >
            <View
                position={'relative'}
                paddingX={'size-175'}
                paddingY={'size-125'}
                borderTopWidth={'thin'}
                borderTopEndRadius={'regular'}
                borderTopStartRadius={'regular'}
                borderTopColor={'gray-200'}
                backgroundColor={'gray-200'}
                minHeight={minHeight ?? 'size-1000'}
                UNSAFE_style={{ boxSizing: 'border-box' }}
                UNSAFE_className={isSelected ? classes.selectedHeader : ''}
            >
                <Flex direction={'column'} width={'100%'} height={'100%'} justifyContent={'center'}>
                    {headerContent}
                </Flex>
            </View>
            <View
                paddingX={'size-250'}
                paddingY={'size-225'}
                borderBottomWidth={'thin'}
                borderBottomEndRadius={'regular'}
                borderBottomStartRadius={'regular'}
                borderBottomColor={'gray-100'}
                height={'size-1000'}
                UNSAFE_className={[
                    classes.selectableCardDescription,
                    isSelected ? classes.selectedDescription : '',
                ].join(' ')}
            >
                {descriptionContent}
            </View>
        </div>
    );
};
