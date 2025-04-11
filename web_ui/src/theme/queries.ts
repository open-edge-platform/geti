// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

const largeSize = 1025;
const mediumLargeSize = 1300;
const extraLargeSize = 1500;

export const smallerThanQuery = (pixels: string) => `(max-width: ${pixels}px)`;
export const biggerThanQuery = (pixels: string) => `(min-width: ${pixels}px)`;
export const isLargeSizeQuery = `(min-width: ${largeSize}px)`;
export const isMediumLargeSizeQuery = `(min-width: ${largeSize + 1}px) and (max-width: ${mediumLargeSize}px)`;
export const isExtraLargeSizeQuery = `(min-width: ${extraLargeSize + 1}px)`;
