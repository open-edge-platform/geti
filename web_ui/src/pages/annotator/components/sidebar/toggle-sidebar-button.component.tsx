// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { Flex, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { PressableElement } from '@geti/ui';
import { useToggleState } from '@react-stately/toggle';
import { ToggleProps } from '@react-types/checkbox';
import ChevronDoubleLeft from '@spectrum-icons/workflow/ChevronDoubleLeft';
import ChevronDoubleRight from '@spectrum-icons/workflow/ChevronDoubleRight';
import { useToggleButton } from 'react-aria';

import classes from './toggle-sidebar.module.scss';

export const ToggleSidebarButton = (props: ToggleProps): JSX.Element => {
    const ref = useRef<HTMLButtonElement>(null);
    const state = useToggleState(props);
    const { buttonProps } = useToggleButton(props, state, ref);

    return (
        <button
            {...buttonProps}
            ref={ref}
            className={classes.toggleSidebarButton}
            id='annotations-pane-sidebar-toggle-button'
        >
            <View backgroundColor='gray-100' paddingY='size-50' paddingX='size-150'>
                <Flex height='100%' justifyContent='end'>
                    <TooltipTrigger placement={'bottom'}>
                        <PressableElement onPress={state.toggle}>
                            {props.isSelected ? <ChevronDoubleRight size='XS' /> : <ChevronDoubleLeft size='XS' />}
                        </PressableElement>
                        <Tooltip>{props.isSelected ? 'Collapse sidebar' : 'Open sidebar'}</Tooltip>
                    </TooltipTrigger>
                </Flex>
            </View>
        </button>
    );
};
