// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export function assertIsNotNullable<T>(value: T | null | undefined): asserts value is T {
    if (value === null || value === undefined) {
        throw new Error(`${value} must not be null or undefined`);
    }
}
