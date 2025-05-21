// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { ActionButton } from '@geti/ui';
import { Collapse, Expand } from '@geti/ui/icons';

interface FullscreenProps {
    enabled: boolean;
    toggle: Dispatch<SetStateAction<boolean>>;
}

export const Fullscreen = ({ enabled, toggle }: FullscreenProps): JSX.Element => {
    return (
        <ActionButton
            isQuiet
            justifySelf='end'
            id='job-scheduler-action-expand'
            data-testid='job-scheduler-action-expand'
            aria-label='Job scheduler action expand'
            onPress={() => toggle((prevState: boolean) => !prevState)}
        >
            {!enabled ? <Expand /> : <Collapse />}
        </ActionButton>
    );
};
