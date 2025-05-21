// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { Flex, Heading } from '@geti/ui';
import { SortUp } from '@geti/ui/icons';
import { motion } from 'framer-motion';
import { usePress } from 'react-aria';

import { SortDirection } from '../../../core/shared/query-parameters';

import classes from './sort-by-attribute.module.scss';

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
