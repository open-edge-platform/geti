// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const distributeByLargestRemainder = (values: number[], total: number): number[] => {
    const sum = values.reduce((acc, value) => acc + value, 0);

    if (sum <= 0 || total <= 0) {
        return values.map(() => 0);
    }

    const exactShares = values.map((value) => (value / sum) * total);
    const flooredShares = exactShares.map((share) => Math.floor(share));
    let remainder = total - flooredShares.reduce((acc, value) => acc + value, 0);

    const indicesByRemainder = exactShares
        .map((share, index) => ({ index, fractional: share - Math.floor(share) }))
        .sort((a, b) => b.fractional - a.fractional);

    const result = [...flooredShares];
    for (const { index } of indicesByRemainder) {
        if (remainder <= 0) break;
        result[index] += 1;
        remainder -= 1;
    }

    return result;
};
