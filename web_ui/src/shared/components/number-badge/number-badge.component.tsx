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

import { Text, useNumberFormatter, View, ViewProps } from '@adobe/react-spectrum';
import { StyleProps } from '@react-types/shared';

import { LoadingIndicator } from '../loading/loading-indicator.component';

import classes from '../number-badge/number-badge.module.scss';

interface NumberBadgeProps {
    id: string;
    jobsNumber: number | null;
    isPending?: boolean;
    isAccented?: boolean;
    isSelected?: boolean;
}

interface CircleBadgeProps extends StyleProps {
    children: JSX.Element;
    id?: string;
    backgroundColor?: ViewProps<5>['backgroundColor'];
}

const CircleBadge = ({ children, ...viewProps }: CircleBadgeProps): JSX.Element => {
    return (
        <View {...viewProps} borderRadius={'large'} width={'size-200'} height={'size-200'}>
            {children}
        </View>
    );
};

const getNumberClasses = (number: number): string => {
    const size = number >= 100 ? 'large' : number >= 10 ? 'medium' : '';

    if (size) {
        return `${classes.number} ${classes[size]}`;
    }

    return classes.number;
};

export const NumberBadge = ({
    id,
    jobsNumber,
    isPending,
    isSelected = false,
    isAccented = false,
}: NumberBadgeProps): JSX.Element => {
    const formatter = useNumberFormatter({ notation: 'compact' });

    if (isPending || jobsNumber === null) {
        return <LoadingIndicator size={'S'} />;
    }

    return (
        <>
            {jobsNumber === 0 ? (
                <></>
            ) : (
                <CircleBadge
                    id={`number-badge-${id}`}
                    data-testid='number badge'
                    UNSAFE_className={`${classes.circle} ${
                        isAccented ? classes.accented : isSelected ? classes.selected : classes.basic
                    }`}
                >
                    <Text data-testid={`number-badge-${id}-value`} UNSAFE_className={getNumberClasses(jobsNumber)}>
                        {formatter.format(jobsNumber)}
                    </Text>
                </CircleBadge>
            )}
        </>
    );
};
