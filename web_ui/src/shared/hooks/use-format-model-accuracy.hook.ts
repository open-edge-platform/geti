// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useNumberFormatter } from 'react-aria';

export const useFormatModelAccuracy = (accuracy: number | null | undefined): string => {
    const formatter = useNumberFormatter({ style: 'percent', maximumFractionDigits: 1 });

    return accuracy != null ? formatter.format(accuracy) : '-';
};
