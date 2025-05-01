// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, FC } from 'react';

import { ActionButton } from '@shared/components/button/button.component';

import { Refresh } from '../../../../../../../assets/icons';

type ResetButtonProps = Omit<ComponentProps<typeof ActionButton>, 'children' | 'isQuiet'>;

export const ResetButton: FC<ResetButtonProps> = (props) => {
    return (
        <ActionButton isQuiet {...props}>
            <Refresh />
        </ActionButton>
    );
};
