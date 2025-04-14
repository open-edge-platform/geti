// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SpectrumActionButtonProps } from '@react-types/button';

import { Accept } from '../../../assets/icons';
import { ActionButton } from '../button/button.component';

import sharedClasses from '../../shared.module.scss';

export const AcceptButton = (props: SpectrumActionButtonProps) => {
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
