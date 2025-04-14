// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface ConfusionMatrixProps {
    columnHeader: string;
    rowHeader: string;
    columnNames: string[];
    rowNames: string[];
    matrixValues: number[][];
    size: number;
    ratio?: number;
}
