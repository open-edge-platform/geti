// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
