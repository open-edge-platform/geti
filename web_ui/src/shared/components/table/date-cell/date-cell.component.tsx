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

import { Flex, Text } from '@adobe/react-spectrum';

import { formatDate } from '../../../utils';

import classes from './date-cell.module.scss';

interface DateCellProps {
    id?: string;
    date: string;
    direction?: 'column' | 'row';
}

export const DateCell = ({ id, date, direction = 'column' }: DateCellProps): JSX.Element => {
    return (
        <Flex id={id} direction={direction}>
            <Text UNSAFE_className={direction === 'row' ? classes.date : ''}>{formatDate(date, 'DD MMM YYYY')}</Text>
            <Text UNSAFE_className={direction === 'column' ? classes.hour : ''}>{formatDate(date, 'hh:mm A')}</Text>
        </Flex>
    );
};
