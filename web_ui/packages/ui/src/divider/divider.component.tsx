// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider as SpectrumDivider, SpectrumDividerProps } from '@adobe/react-spectrum';

import classes from './divider.module.scss';

export const Divider = (props: SpectrumDividerProps) => {
    return <SpectrumDivider UNSAFE_className={classes.divider} {...props} />;
};
