// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, RefObject, useRef, useState } from 'react';

import { DOMRefValue, useUnwrapDOMRef } from '@geti/ui';
import { useHover, useInteractOutside } from '@react-aria/interactions';
import clsx from 'clsx';

import { KeypointNode, Point } from '../../../../../core/annotations/shapes.interface';
import { CursorContextMenu } from './cursor-context-menu/cursor-context-menu.component';
import { HiddenEdge } from './hidden-edge.component';

import classes from './edge.module.scss';

export interface EdgeProps {
    id?: string;
    to: KeypointNode;
    from: KeypointNode;
    isSelected: boolean;
    isDisabled?: boolean;
    contextMenu?: ReactNode;
    onSelect: (isSelected: boolean) => void;
    onRemoveSelected: (id: string) => void;
    onResetAndSelect: (id: string[]) => void;
    onNewIntermediatePoint: (newPoint: Point, prevFrom: KeypointNode, prevTo: KeypointNode) => void;
}

interface InteractOutsideProps {
    triggerRef: React.RefObject<SVGGElement>;
    containerRef: RefObject<HTMLElement | null>;
    onClickOutside: (target: Element) => void;
}

// Keypoints have their own logic for selecting edge points. To avoid collisions and potential unwanted behavior,
// we refrain from deselecting them here and allow the canvas-template logic to handle it instead
const isKeypoint = (element: Element) => {
    return /^resize keypoint/i.test(element.getAttribute('aria-label') ?? '');
};

const isHiddenEdge = (element: Element) => {
    return /^hidden padded edge/i.test(element.getAttribute('aria-label') ?? '');
};

const useContextMenuState = (isSelected: boolean): [boolean, React.Dispatch<React.SetStateAction<boolean>>] => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    if (isMenuOpen && !isSelected) {
        setIsMenuOpen(false);
    }

    return [isMenuOpen, setIsMenuOpen];
};

const InteractOutside = ({ triggerRef, containerRef, onClickOutside }: InteractOutsideProps) => {
    useInteractOutside({
        ref: triggerRef,
        onInteractOutside: (event) => {
            const target = event.target as Element;

            if (containerRef.current?.contains(target)) {
                return;
            }

            onClickOutside(target);
        },
    });
    return <></>;
};

export const Edge = ({
    id = '',
    to,
    from,
    isSelected,
    contextMenu,
    isDisabled = false,
    onSelect,
    onRemoveSelected,
    onResetAndSelect,
    onNewIntermediatePoint,
}: EdgeProps) => {
    const triggerRef = useRef<SVGGElement>(null);
    const contextMenuRef = useRef<DOMRefValue>(null);
    const { hoverProps, isHovered } = useHover({});
    const unwrappedContextMenuRef = useUnwrapDOMRef(contextMenuRef);
    const [isMenuOpen, setIsMenuOpen] = useContextMenuState(isSelected);

    const position = { x1: from.x, y1: from.y, x2: to.x, y2: to.y };

    const handleOpen = () => {
        setIsMenuOpen(true);
        onResetAndSelect([id]);
    };

    return (
        <>
            {isSelected && (
                <InteractOutside
                    triggerRef={triggerRef}
                    containerRef={unwrappedContextMenuRef}
                    onClickOutside={(target) => {
                        !isKeypoint(target) && onRemoveSelected(id);
                        setIsMenuOpen(false);
                    }}
                />
            )}
            <g
                ref={triggerRef}
                style={{ pointerEvents: isDisabled ? 'none' : 'auto' }}
                aria-label='edge container'
                {...hoverProps}
            >
                <line
                    aria-label={`line - ${from.label.name}`}
                    {...position}
                    style={{ stroke: from.label.color }}
                    className={clsx({
                        [classes.edge]: true,
                        [classes.selected]: isSelected,
                        [classes.secondLine]: true,
                    })}
                />

                <line
                    aria-label={`line - ${to.label.name}`}
                    {...position}
                    style={isSelected ? { stroke: to.label.color } : {}}
                    className={clsx({
                        [classes.edge]: true,
                        [classes.selected]: isSelected,
                        [classes.hovered]: isHovered,
                    })}
                />

                <HiddenEdge
                    to={to}
                    from={from}
                    isHovered={isHovered}
                    isSelected={isSelected}
                    onSelect={onSelect}
                    onNewIntermediatePoint={onNewIntermediatePoint}
                />

                <CursorContextMenu
                    isOpen={isMenuOpen}
                    triggerRef={triggerRef}
                    containerRef={contextMenuRef}
                    onOpen={handleOpen}
                    isValidTrigger={isHiddenEdge}
                >
                    {contextMenu}
                </CursorContextMenu>
            </g>
        </>
    );
};
