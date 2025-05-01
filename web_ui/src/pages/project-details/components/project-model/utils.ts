// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { formatDate } from '@shared/utils';
import dayjs from 'dayjs';

export const getVersionWithDateText = (version: number, creationDate: string): string => {
    return `Version ${version} (${creationDate && formatDate(dayjs(creationDate).toString(), 'DD MMM YY')})`;
};
