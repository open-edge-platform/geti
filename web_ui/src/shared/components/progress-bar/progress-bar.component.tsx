// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { ProgressBar as SpectrumProgressBar } from '@geti/ui';
import { SpectrumProgressBarProps } from '@react-types/progress';

interface ProgressBarProps extends SpectrumProgressBarProps {
    value: number;
    animationTime?: number;
}

export const ProgressBar = (props: ProgressBarProps): JSX.Element => {
    const { value, animationTime = 100 } = props;
    const [animatedValue, setAnimatedValue] = useState<number>(0);

    useEffect(() => {
        const id = setTimeout(() => {
            setAnimatedValue(value);
        }, animationTime);

        return () => clearTimeout(id);
    }, [animationTime, value]);

    return <SpectrumProgressBar {...props} value={animatedValue} />;
};
