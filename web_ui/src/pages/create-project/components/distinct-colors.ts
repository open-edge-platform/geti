// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export const getHEXFormat = (color: string): string => {
    const regex = /^[#]*.{6}[f]{2}/g;
    const found = color.match(regex);

    return found ? color.slice(0, 7) : color;
};

// Get a distinct color by generating a hash from the provided string using method provided by,
// https://gist.github.com/hyamamoto/fd435505d29ebfa3d9716fd2be8d42f0?permalink_comment_id=2800233#gistcomment-2800233
export const getDistinctColorBasedOnHash = (value: string): string => {
    const hash = Array.from(value).reduce((s, c) => (Math.imul(31, s) + c.charCodeAt(0)) | 0, 0);

    const index = ((hash % DISTINCT_COLORS.length) + DISTINCT_COLORS.length) % DISTINCT_COLORS.length;

    return DISTINCT_COLORS[index];
};

export const getRandomDistinctColor = (): string => DISTINCT_COLORS[Math.floor(Math.random() * DISTINCT_COLORS.length)];

export const DISTINCT_COLORS = [
    '#708541',
    '#E96115',
    '#EDB200',
    '#FF5662',
    '#CC94DA',
    '#5B69FF',
    '#548FAD',
    //
    '#25A18E',
    '#9D3B1A',
    '#C9E649',
    '#F15B85',
    '#81407B',
    '#26518E',
    '#076984',
    //
    '#00F5D4',
    '#FF7D00',
    '#F7DAB3',
    '#80E9AF',
    '#9B5DE5',
    '#00A5CF',
    '#D7BC5E',
];
