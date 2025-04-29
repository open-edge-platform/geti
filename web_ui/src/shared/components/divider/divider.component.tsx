// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider as SpectrumDivider } from '@adobe/react-spectrum';
import { SpectrumDividerProps } from '@react-types/divider';

import classes from './divider.module.scss';

export const Divider = (props: SpectrumDividerProps) => {
    return <SpectrumDivider UNSAFE_className={classes.divider} {...props} />;
};
