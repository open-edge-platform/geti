// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, RefObject, useContext, useRef, useState } from 'react';

import { Flex, FlexProps, Grid } from '@adobe/react-spectrum';
import { useInteractOutside } from '@react-aria/interactions';
import { useUnwrapDOMRef } from '@react-spectrum/utils';
import clsx from 'clsx';

import classes from './list-item-grid.module.scss';

interface ListItemGridProps {
    id: string;
    isLast: boolean;
    isSelected: boolean;
    ariaLabel: string;
    children: ReactNode;
    onHoverEnd: () => void;
    onHoverStart: () => void;
}

interface ListItemGridContextProps {
    isHovered: boolean;
    setIsHovered: (isHovered: boolean) => void;
}

interface InteractOutsideProps {
    containerRef: RefObject<HTMLElement | null>;
    onClickOutside: () => void;
}

const ListItemGridContext = createContext<ListItemGridContextProps>({ isHovered: false, setIsHovered: () => {} });

const useListItemGridContext = () => useContext(ListItemGridContext);

const InteractOutside = ({ containerRef, onClickOutside }: InteractOutsideProps) => {
    useInteractOutside({
        ref: containerRef,
        onInteractOutside: (event) => {
            const target = event.target as Element;
            if (containerRef.current?.contains(target)) {
                return;
            }
            // add a timeout to ensure this executes after menu-related events are processed
            setTimeout(onClickOutside, 0);
        },
    });
    return <></>;
};

export const ListItemGrid = ({
    id,
    isLast,
    children,
    ariaLabel,
    isSelected,
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
                [classes.selectedAnnotation]: isSelected || isHovered,
            })}
        >
            <ListItemGridContext.Provider value={{ isHovered, setIsHovered }}>
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
    const containerRef = useRef<null>(null);
    const unwrapContainerRef = useUnwrapDOMRef(containerRef);
    const { isHovered, setIsHovered } = useListItemGridContext();

    if (!isHovered) {
        return <></>;
    }

    return (
        <>
            <Flex {...otherProps} gridArea={'list-menu'} ref={containerRef}>
                {children}
            </Flex>
            <InteractOutside containerRef={unwrapContainerRef} onClickOutside={() => setIsHovered(false)} />
        </>
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
