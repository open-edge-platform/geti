// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const apiRequestUrl = (url: string): string => {
    const urlRecord = new URL(`http://localhost/${url}`);
    urlRecord.search = '';

    return urlRecord.href;
};
