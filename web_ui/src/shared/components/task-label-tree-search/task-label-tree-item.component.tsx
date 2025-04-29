// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, DetailedHTMLProps, HTMLAttributes, ReactNode, useState } from 'react';

import { Flex, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import isFunction from 'lodash/isFunction';
import { useHover, usePress } from 'react-aria';

import { ChevronDownSmallLight, ChevronRightSmallLight } from '../../../assets/icons';
import { LabelItemType, LabelTreeItem, LabelTreeLabelProps } from '../../../core/labels/label-tree-view.interface';
import { Label } from '../../../core/labels/label.interface';
import { getLabelId } from '../../../core/labels/utils';
import { ActionButton } from '../button/button.component';
import { LabelColorThumb } from '../label-color-thumb/label-color-thumb.component';
import { PressableElement } from '../pressable-element/pressable-element.component';
import { groupTitleStyles, LABEL_GAP, VIEW_GAP } from './utils';

export interface SearchLabelTreeItemSuffix {
    (label: LabelTreeLabelProps, { isHovered }: { isHovered: boolean }): ReactNode;
}

interface TaskLabelTreeItemProps {
    level: number;
    label: LabelTreeItem;
    children: ReactNode;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
    onClick?: (label: Label) => void;
}

interface TaskLabelTreeItemLabelProps {
    label: LabelTreeLabelProps;
    leftGap: number;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
    onClick?: (label: Label) => void;
}

const getItemStyles = (leftGap: number, otherStyles?: CSSProperties): CSSProperties => ({
    boxSizing: 'border-box',
    paddingLeft: dimensionValue(leftGap),
    paddingRight: dimensionValue('size-200'),
    borderBottom: '1px solid var(--spectrum-global-color-gray-200)',
    ...otherStyles,
});

const BaseTruncatedText = (props: DetailedHTMLProps<HTMLAttributes<HTMLSpanElement>, HTMLSpanElement>) => (
    <span {...props} style={{ overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis', ...props.style }}>
        {props.children}
    </span>
);

const TaskLabelTreeItemLabel = ({
    label,
    leftGap,
    onClick,
    suffix = () => <></>,
    prefix = () => <></>,
}: TaskLabelTreeItemLabelProps) => {
    const labelId = getLabelId('tree', label);

    const { hoverProps, isHovered } = useHover({});
    const { pressProps } = usePress({
        onPress: () => isFunction(onClick) && onClick(label),
    });

    return (
        <div
            {...pressProps}
            {...hoverProps}
            style={getItemStyles(leftGap, {
                cursor: isFunction(onClick) ? 'pointer' : 'default',
                backgroundColor: isHovered ? 'rgba(255, 255, 255, 0.03)' : undefined,
            })}
        >
            <Flex gap={'size-150'} height={'size-400'} alignItems={'center'}>
                {prefix(label, { isHovered })}

                <LabelColorThumb label={label} id={`${labelId}-color`} />
                <BaseTruncatedText id={labelId}>{label.name}</BaseTruncatedText>

                {suffix(label, { isHovered })}
            </Flex>
        </div>
    );
};

export const TaskLabelTreeItem = ({ label, children, level, suffix, prefix, onClick }: TaskLabelTreeItemProps) => {
    const [isOpen, setIsOpen] = useState(label.open);
    const isGroup = label.type === LabelItemType.GROUP;
    const leftGap = VIEW_GAP * level;

    return (
        <li id={`label-item-${label.id}`} aria-label={`label item ${label.name}`}>
            {isGroup && (
                <Flex gap={'size-150'} height={'size-400'} alignItems={'center'} UNSAFE_style={getItemStyles(leftGap)}>
                    <ActionButton
                        isQuiet
                        width={16}
                        onPress={() => setIsOpen((open) => !open)}
                        aria-label={`toggleable chevron ${label.id}`}
                    >
                        {isOpen ? (
                            <ChevronDownSmallLight aria-label='label open' />
                        ) : (
                            <ChevronRightSmallLight aria-label='label close' />
                        )}
                    </ActionButton>

                    <BaseTruncatedText style={groupTitleStyles}>{label.name}</BaseTruncatedText>

                    <View UNSAFE_style={groupTitleStyles} marginStart={'auto'} marginEnd={'size-125'}>
                        <TooltipTrigger placement={'bottom'}>
                            <PressableElement aria-label='label-relation'>{label.relation[0]}</PressableElement>
                            <Tooltip>{label.relation}</Tooltip>
                        </TooltipTrigger>
                    </View>
                </Flex>
            )}

            {!isGroup && (
                <TaskLabelTreeItemLabel
                    label={{ ...(label as LabelTreeLabelProps) }}
                    leftGap={leftGap + LABEL_GAP}
                    suffix={suffix}
                    prefix={prefix}
                    onClick={onClick}
                />
            )}

            {isOpen && children}
        </li>
    );
};
