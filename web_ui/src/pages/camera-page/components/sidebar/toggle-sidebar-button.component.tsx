// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { ActionButton, Tooltip, TooltipTrigger } from '@geti/ui';
import { ChevronDoubleLeft, ChevronDoubleRight } from '@geti/ui/icons';

import classes from './sidebar.module.scss';

interface ToggleSidebarButtonProps extends Pick<ComponentProps<typeof ActionButton>, 'flex'> {
    isOpen: boolean;
    onIsOpenChange: () => void;
}

export const ToggleSidebarButton = ({ isOpen, onIsOpenChange, flex }: ToggleSidebarButtonProps) => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                isQuiet
                flex={flex}
                onPress={onIsOpenChange}
                aria-label={'toggle sidebar'}
                UNSAFE_className={classes.toggleSidebarButton}
            >
                {isOpen ? <ChevronDoubleRight size='XS' /> : <ChevronDoubleLeft size='XS' />}
            </ActionButton>
            <Tooltip>{isOpen ? 'Collapse sidebar' : 'Open sidebar'}</Tooltip>
        </TooltipTrigger>
    );
};
