// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const chunkArray = <T>(array: T[], size: number): T[][] => {
    const chunkedArray: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
        chunkedArray.push(array.slice(i, i + size));
    }
    return chunkedArray;
};
