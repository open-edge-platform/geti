// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

const largeSize = 1025;
const mediumLargeSize = 1300;
const extraLargeSize = 1500;

export const smallerThanQuery = (pixels: string) => `(max-width: ${pixels}px)`;
export const biggerThanQuery = (pixels: string) => `(min-width: ${pixels}px)`;
export const isLargeSizeQuery = `(min-width: ${largeSize}px)`;
export const isMediumLargeSizeQuery = `(min-width: ${largeSize + 1}px) and (max-width: ${mediumLargeSize}px)`;
export const isExtraLargeSizeQuery = `(min-width: ${extraLargeSize + 1}px)`;
