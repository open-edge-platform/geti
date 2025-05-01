// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode, useState } from 'react';

import { Flex, Grid, Text, View } from '@adobe/react-spectrum';
import { ActionButton } from '@shared/components/button/button.component';
import { LabelColorThumb } from '@shared/components/label-color-thumb/label-color-thumb.component';
import { TruncatedTextWithTooltip } from '@shared/components/truncated-text/truncated-text.component';
import isEmpty from 'lodash/isEmpty';
import { useHover, usePress } from 'react-aria';

import { Expanded } from '../../../../../assets/icons';
import { LabelTreeLabelProps } from '../../../../../core/labels/label-tree-view.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { getLabelId } from '../../../../../core/labels/utils';

import classes from './search-label-tree-view-item.module.scss';

export interface SearchLabelTreeItemSuffix {
    (label: LabelTreeLabelProps, { isHovered }: { isHovered: boolean }): ReactNode;
}

interface SearchLabelTreeViewItemProps {
    label: LabelTreeLabelProps;
    clickHandler: (label: Label) => void;
    children: ReactNode;
    light?: boolean;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
}

export const ToggleableChevron = ({ isOpen, toggle, id }: { isOpen: boolean; toggle: () => void; id: string }) => {
    return (
        <ActionButton
            isQuiet
            id={id}
            data-testid={`chevron-${id}`}
            aria-label={isOpen ? 'Click to hide child labels' : 'Click to show child labels'}
            onPress={toggle}
            height='auto'
            width='16px'
            UNSAFE_style={{
                padding: '0',
                margin: '0',
                width: '16px',
            }}
            marginStart={'-8px'}
        >
            <View
                UNSAFE_style={{
                    transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)',
                    transition: 'transform 0.25s',
                }}
            >
                <Expanded />
            </View>
        </ActionButton>
    );
};

export const SearchLabelTreeViewItem = ({
    label,
    clickHandler,
    children,
    suffix,
    prefix,
}: SearchLabelTreeViewItemProps): JSX.Element => {
    const { name, hotkey } = label;
    const { hoverProps, isHovered } = useHover({});

    const [isOpen, setIsOpen] = useState<boolean>(label.open);
    const pressHandler = { onPress: () => clickHandler(label) };
    const { pressProps } = usePress({ ...pressHandler });

    return (
        <li
            className={`${classes['spectrum-TreeView-item']} ${isOpen ? classes['is-open'] : classes.isClosed} `}
            id={`label-item-${label.id}`}
            aria-label={`label item ${label.name}`}
            {...pressProps}
        >
            <View
                UNSAFE_className={[
                    classes['spectrum-TreeView-itemLink'],
                    classes.adjustableHeight,
                    classes.labelTreeItem,
                ].join(' ')}
                paddingX={'size-200'}
                backgroundColor={isHovered ? 'gray-100' : undefined}
            >
                <Grid columns={isEmpty(label.children) ? ['1fr'] : ['size-200', '1fr']} gap='size-100' width='100%'>
                    {label.children.length > 0 ? (
                        <ToggleableChevron
                            isOpen={isOpen}
                            toggle={() => {
                                setIsOpen((open: boolean) => !open);
                            }}
                            id={label.id}
                        />
                    ) : (
                        <></>
                    )}
                    <div {...hoverProps} className={classes.listItem}>
                        {prefix && prefix(label, { isHovered })}

                        <LabelColorThumb label={label} id={`${getLabelId('tree', label)}-color`} />

                        <Flex direction={'column'} flexGrow={1} maxWidth={'size-2000'} marginEnd={'auto'}>
                            <TruncatedTextWithTooltip id={getLabelId('tree', label)} {...pressHandler}>
                                {name}
                            </TruncatedTextWithTooltip>
                        </Flex>

                        {suffix ? (
                            suffix(label, { isHovered })
                        ) : hotkey ? (
                            <Text id={`label-hotkey-${name}`}>{hotkey.toUpperCase()}</Text>
                        ) : (
                            <></>
                        )}
                    </div>
                </Grid>
            </View>

            {children}
        </li>
    );
};
