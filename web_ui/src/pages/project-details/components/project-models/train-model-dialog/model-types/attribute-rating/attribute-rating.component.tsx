// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, Heading, View } from '@adobe/react-spectrum';

import classes from './attribute-rating.module.scss';

export type Ratings = 'LOW' | 'MEDIUM' | 'HIGH';

interface RateProps {
    color: string;
}

const RateColorPalette = {
    LOW: 'var(--energy-blue-tint2)',
    MEDIUM: 'var(--energy-blue-tint1)',
    HIGH: 'var(--energy-blue)',
    EMPTY: 'var(--spectrum-global-color-gray-500)',
};

const RateColors = {
    LOW: [RateColorPalette.LOW, RateColorPalette.EMPTY, RateColorPalette.EMPTY],
    MEDIUM: [RateColorPalette.LOW, RateColorPalette.MEDIUM, RateColorPalette.EMPTY],
    HIGH: [RateColorPalette.LOW, RateColorPalette.MEDIUM, RateColorPalette.HIGH],
};

const Rate: FC<RateProps> = ({ color }) => {
    return (
        <View
            UNSAFE_className={classes.rate}
            UNSAFE_style={{
                backgroundColor: color,
            }}
        />
    );
};

interface AttributeRatingProps {
    name: string;
    rating: Ratings;
}

export const AttributeRating: FC<AttributeRatingProps> = ({ name, rating }) => {
    return (
        <Flex direction={'column'} gap={'size-100'} justifyContent={'space-between'}>
            <Heading margin={0} UNSAFE_className={classes.attributeRatingTitle}>
                {name}
            </Heading>
            <Flex alignItems={'center'} gap={'size-100'}>
                {RateColors[rating].map((color, idx) => (
                    <Rate key={idx} color={color} />
                ))}
            </Flex>
        </Flex>
    );
};
