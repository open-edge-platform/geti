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

import { createContext, ReactNode, useContext } from 'react';

import { Flex, FlexProps, Grid } from '@adobe/react-spectrum';
import clsx from 'clsx';
import { useHover } from 'react-aria';

import classes from './list-item-grid.module.scss';

interface ListItemGridProps {
    id: string;
    isLast: boolean;
    isSelected: boolean;
    isDragging: boolean;
    ariaLabel: string;
    children: ReactNode;
    onHoverEnd: () => void;
    onHoverStart: () => void;
}

const ListItemGridContext = createContext({ isHovered: false });

const useListItemGridContext = () => useContext(ListItemGridContext);

export const ListItemGrid = ({
    id,
    isLast,
    children,
    ariaLabel,
    isSelected,
    isDragging,
    onHoverStart,
    onHoverEnd,
}: ListItemGridProps) => {
    const { hoverProps, isHovered } = useHover({ onHoverStart, onHoverEnd });

    return (
        <div
            {...hoverProps}
            id={id}
            role={'listitem'}
            aria-label={ariaLabel}
            className={clsx({
                [classes.annotationItem]: true,
                [classes.lastAnnotationItem]: isLast,
                [classes.selectedAnnotation]: isSelected || isHovered || isDragging,
            })}
        >
            <ListItemGridContext.Provider value={{ isHovered }}>
                <Grid
                    justifyContent={'left'}
                    alignItems={'center'}
                    minHeight={'size-400'}
                    columns={['auto', 'auto', '1fr', 'auto', 'auto']}
                    areas={['checkbox color labels list-menu actions-menu']}
                >
                    {children}
                </Grid>
            </ListItemGridContext.Provider>
        </div>
    );
};

const Checkbox = ({ children, ...otherProps }: FlexProps) => {
    return (
        <Flex {...otherProps} gridArea={'checkbox'}>
            {children}
        </Flex>
    );
};

const Color = ({ children, ...otherProps }: FlexProps) => {
    return (
        <Flex {...otherProps} gridArea={'color'}>
            {children}
        </Flex>
    );
};

const Labels = ({ children, ...otherProps }: FlexProps) => {
    return (
        <Flex {...otherProps} gridArea={'labels'}>
            {children}
        </Flex>
    );
};

const ListMenu = ({ children, ...otherProps }: FlexProps) => {
    const { isHovered } = useListItemGridContext();

    if (!isHovered) {
        return <></>;
    }

    return (
        <Flex {...otherProps} gridArea={'list-menu'}>
            {children}
        </Flex>
    );
};

const ActionsMenu = ({ children, ...otherProps }: FlexProps) => {
    return (
        <Flex {...otherProps} gridArea={'actions-menu'}>
            {children}
        </Flex>
    );
};

ListItemGrid.ListMenu = ListMenu;
ListItemGrid.Checkbox = Checkbox;
ListItemGrid.Color = Color;
ListItemGrid.Labels = Labels;
ListItemGrid.ActionsMenu = ActionsMenu;
