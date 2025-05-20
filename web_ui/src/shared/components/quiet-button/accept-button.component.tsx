// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, type ActionButtonProps } from '@geti/ui';
import { Accept } from '@geti/ui/icons';

import sharedClasses from '../../shared.module.scss';

export const AcceptButton = (props: ActionButtonProps) => {
    return (
        <ActionButton
            isQuiet
            {...props}
            UNSAFE_className={`${sharedClasses.acceptButton} ${props.UNSAFE_className ?? ''}`}
        >
            <Accept />
        </ActionButton>
    );
};
