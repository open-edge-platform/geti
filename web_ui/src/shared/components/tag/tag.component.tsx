// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Flex, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { PressableElement } from '../pressable-element/pressable-element.component';

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
                <PressableElement>
                    <Text>{text}</Text>
                </PressableElement>
                <Tooltip>{tooltip}</Tooltip>
            </TooltipTrigger>
            {suffix ? <Flex UNSAFE_className={classes.tagSuffix}>{suffix}</Flex> : null}
        </div>
    );
};
