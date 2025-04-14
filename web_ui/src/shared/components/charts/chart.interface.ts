// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface Colors {
    color: string;
    fadedColor: string;
}

export interface ChartData {
    value: number;
    name: string;
}

export interface ChartProps {
    title: string;
    data: ChartData[];
}
