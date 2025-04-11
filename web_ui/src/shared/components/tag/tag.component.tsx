// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { ActionElement } from '../action-element/action-element.component';

import classes from './tag.module.scss';

interface TagProps {
    id?: string;
    text: string;
    prefix?: JSX.Element;
    suffix?: JSX.Element;
    withDot?: boolean;
    className?: string;
    tooltip?: string;
    darkMode?: boolean;
    style?: CSSProperties;
}

/*
    By default the Tag component will display a blue dot before the text.
    This can be disabled by setting `withDot` to false.
    It also supports prefix or suffix elements
*/
export const Tag = ({
    id,
    text,
    prefix,
    suffix,
    className,
    withDot = true,
    tooltip,
    darkMode,
    ...rest
}: TagProps): JSX.Element => {
    const hasPrefix = !!(withDot || prefix);

    return (
        <div
            className={[
                classes.tag,
                !hasPrefix ? classes.noPrefix : '',
                !suffix ? classes.noSuffix : '',
                className,
            ].join(' ')}
            id={id}
            data-testid={id}
            style={{
                backgroundColor: darkMode
                    ? 'var(--spectrum-global-color-gray-100)'
                    : 'var(--spectrum-global-color-gray-200)',
            }}
            aria-label={text}
            {...rest}
        >
            {hasPrefix && (
                <Flex UNSAFE_className={classes.tagPrefix}>
                    {prefix ? prefix : withDot ? <div className={classes.dot} /> : <></>}
                </Flex>
            )}

            <TooltipTrigger placement={'top'} isDisabled={isEmpty(tooltip)}>
                <ActionElement>{text}</ActionElement>
                <Tooltip>{tooltip}</Tooltip>
            </TooltipTrigger>
            {suffix ? <Flex UNSAFE_className={classes.tagSuffix}>{suffix}</Flex> : null}
        </div>
    );
};
