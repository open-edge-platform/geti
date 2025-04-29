// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const idMatchingFormat = (text: string | number): string => {
    if (typeof text === 'string') {
        return text.split(' ').join('-').replace(',', '').toLowerCase();
    }

    return String(text);
};
