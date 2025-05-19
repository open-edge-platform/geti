// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { useDateFormatter, View } from '@geti/ui';
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
