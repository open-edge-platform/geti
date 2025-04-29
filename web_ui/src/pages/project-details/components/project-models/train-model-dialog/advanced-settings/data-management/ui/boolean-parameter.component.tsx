// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, FC } from 'react';

import { Switch } from '../../../../../../../../shared/components/switch/switch.component';

type SwitchProps = ComponentProps<typeof Switch>;

interface BooleanParameterProps
    extends Omit<SwitchProps, 'isEmphasized' | 'aria-label' | 'isSelected' | 'value' | 'onChange'> {
    value: boolean;
    header: string;
    onChange: (isSelected: boolean) => void;
}

export const BooleanParameter: FC<BooleanParameterProps> = ({ value, header, onChange }) => {
    return (
        <Switch isEmphasized isSelected={value} aria-label={`Toggle ${header}`} onChange={onChange}>
            {value ? 'On' : 'Off'}
        </Switch>
    );
};
