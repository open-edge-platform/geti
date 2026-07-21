// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { Content, Dialog, DialogTrigger, DimensionValue, Flex, PressableElement, Text } from '@geti-ui/ui';

import { isNonEmptyString } from '../../shared/util';

import classes from './filter-popover-button.module.scss';

type FilterPopoverButtonProps = {
    ariaLabel: string;
    placeholder: string;
    summary: string | null;
    gap?: DimensionValue;
    width?: DimensionValue;
    minWidth?: DimensionValue;
    maxWidth?: DimensionValue;
    dialogWidth?: DimensionValue;
    dialogMaxWidth?: DimensionValue;
    dialogAriaLabel?: string;
    children: ReactNode;
};

export const FilterPopoverButton = ({
    ariaLabel,
    placeholder,
    summary,
    gap = 'size-40',
    width,
    minWidth,
    maxWidth,
    dialogWidth,
    dialogMaxWidth,
    dialogAriaLabel = ariaLabel,
    children,
}: FilterPopoverButtonProps) => {
    return (
        <DialogTrigger hideArrow type='popover'>
            <PressableElement>
                <div role='button' aria-label={ariaLabel}>
                    <Flex
                        gap={gap}
                        wrap={'wrap'}
                        width={width}
                        minWidth={minWidth}
                        maxWidth={maxWidth}
                        height={'size-400'}
                        alignItems={'center'}
                        UNSAFE_className={classes.filterContainer}
                    >
                        {isNonEmptyString(summary) ? (
                            <Text>{summary}</Text>
                        ) : (
                            <Text UNSAFE_className={classes.searchPlaceholder}>{placeholder}</Text>
                        )}
                    </Flex>
                </div>
            </PressableElement>

            <Dialog
                width={dialogWidth}
                maxWidth={dialogMaxWidth}
                UNSAFE_className={classes.dialog}
                aria-label={dialogAriaLabel}
            >
                <Content>{children}</Content>
            </Dialog>
        </DialogTrigger>
    );
};
