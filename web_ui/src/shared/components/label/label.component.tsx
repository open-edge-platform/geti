// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import classes from './label.module.scss';

interface LabelProps {
    htmlFor?: string;
    children: ReactNode;
}

export const Label = ({ htmlFor, children }: LabelProps): JSX.Element => {
    return (
        <label htmlFor={htmlFor} className={classes.label}>
            {children}
        </label>
    );
};
