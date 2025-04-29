// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';

import { formatDate } from '../../../../shared/utils';

export const getVersionWithDateText = (version: number, creationDate: string): string => {
    return `Version ${version} (${creationDate && formatDate(dayjs(creationDate).toString(), 'DD MMM YY')})`;
};
