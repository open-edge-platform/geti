// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface LineChartData {
    name: string;
    color: string;
    points: {
        x: number;
        y: number;
    }[];
}

export interface LineChartProps {
    title: string;
    data: LineChartData[];
    xAxisLabel: string;
    yAxisLabel: string;
}
