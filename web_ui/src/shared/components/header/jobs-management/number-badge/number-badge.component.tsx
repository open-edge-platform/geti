// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Loading, Text, useNumberFormatter, View, type StyleProps, type ViewProps } from '@geti/ui';

import classes from './number-badge.module.scss';

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
        return <Loading mode='inline' size={'S'} />;
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
