// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useRef } from 'react';

import { useDateFormatter, View } from '@adobe/react-spectrum';
import { AriaCalendarCellProps, useCalendarCell } from '@react-aria/calendar';
import { CalendarState } from '@react-stately/calendar';
import clsx from 'clsx';

import styles from './month-picker.module.scss';

export const CalendarCell = (props: AriaCalendarCellProps & { state: CalendarState; month: number }): JSX.Element => {
    const ref = useRef<HTMLElement>(null);
    const { buttonProps, cellProps, isDisabled, isSelected } = useCalendarCell(props, props.state, ref);
    const monthDateFormatter = useDateFormatter({ month: 'short', timeZone: props.state.timeZone });
    return (
        <View {...cellProps} UNSAFE_className={styles.cellContainer}>
            <span
                {...buttonProps}
                className={clsx(styles.cell, {
                    [styles.selected]: isSelected,
                    [styles.disabled]: isDisabled,
                })}
            >
                {monthDateFormatter.format(props.date.toDate(props.state.timeZone))}
            </span>
        </View>
    );
};
