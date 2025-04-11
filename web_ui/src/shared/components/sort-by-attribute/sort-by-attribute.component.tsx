// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, SetStateAction } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { Heading } from '@react-spectrum/text';
import { motion } from 'framer-motion';
import { usePress } from 'react-aria';

import { SortUp } from '../../../assets/icons';

import classes from './sort-by-attribute.module.scss';

export enum SortDirection {
    ASC = 'asc',
    DESC = 'dsc',
}

interface SortByAttributeProps {
    label?: string;
    sortIconId: string;
    attributeName: string;
    sortDirection: SortDirection;
    setSortDirection: Dispatch<SetStateAction<SortDirection>>;
}

export const SortByAttribute = ({
    sortDirection,
    setSortDirection,
    sortIconId,
    attributeName,
    label = attributeName,
}: SortByAttributeProps): JSX.Element => {
    const { pressProps } = usePress({
        onPress: () =>
            setSortDirection((prevState) => (prevState === SortDirection.ASC ? SortDirection.DESC : SortDirection.ASC)),
    });

    return (
        <Flex gap={'size-100'} alignItems={'center'}>
            <Heading margin={0} level={5} UNSAFE_className={classes.confidenceTextBucket}>
                {label.toUpperCase()}
            </Heading>
            <div {...pressProps} data-testid={sortIconId}>
                <motion.div
                    id={sortIconId}
                    animate={{ rotate: sortDirection === SortDirection.ASC ? 0 : 180 }}
                    className={classes.sortIcon}
                >
                    <SortUp />
                </motion.div>
            </div>
        </Flex>
    );
};
