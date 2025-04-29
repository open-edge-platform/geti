// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useState } from 'react';

import { Flex, FlexProps, Grid } from '@adobe/react-spectrum';
import clsx from 'clsx';

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
    const [isHovered, setIsHovered] = useState(false);

    const handlePointerOver = () => {
        onHoverStart();
        setIsHovered(true);
    };

    const handlePointerOut = () => {
        onHoverEnd();
        setIsHovered(false);
    };

    return (
        <div
            id={id}
            onPointerOver={handlePointerOver}
            onPointerOut={handlePointerOut}
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
