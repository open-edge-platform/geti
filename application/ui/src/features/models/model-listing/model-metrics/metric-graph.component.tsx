// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import React, { useCallback, useMemo, useRef } from 'react';

import { ActionButton, DOMRefValue, Flex, useUnwrapDOMRef, View } from '@geti-ui/ui';
import { DownloadIcon } from '@geti-ui/ui/icons';
import { CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts';

import { Box } from '../components/box/box.component';

export type MetricGraphPoint = {
    x: number;
    y: number;
};

type MetricGraphProps = {
    title: string;
    data?: MetricGraphPoint[];
    xAxisLabel?: string;
    yAxisLabel: string;
};

const X_AXIS_TICK_COUNT = 8;
const Y_AXIS_TICK_COUNT = 4;

export const MetricGraph = ({ title, data, xAxisLabel, yAxisLabel }: MetricGraphProps) => {
    const graphRef = useRef<DOMRefValue<HTMLDivElement>>(null);
    const unwrappedGraphRef = useUnwrapDOMRef(graphRef);

    const chartData = useMemo(() => {
        if (!data || data.length === 0) return [];
        // Ensure the line starts from zero epoch (x=0)
        if (data[0].x > 0) {
            return [{ x: 0, y: 0 }, ...data];
        }
        return data;
    }, [data]);

    const handleDownload = useCallback(() => {
        if (!unwrappedGraphRef.current) return;

        const svgElement = unwrappedGraphRef.current.querySelector('svg');
        if (!svgElement) return;

        // Clone the SVG so we don't modify the original
        const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;

        // Ensure inline styles are applied correctly by setting explicit width/height
        const bbox = svgElement.getBBox();
        const width = bbox.width + Math.abs(bbox.x);
        const height = bbox.height + Math.abs(bbox.y);

        clonedSvg.setAttribute('width', `${width}`);
        clonedSvg.setAttribute('height', `${height}`);
        clonedSvg.setAttribute('viewBox', `${bbox.x} ${bbox.y} ${width} ${height}`);

        // Inline computed styles to ensure CSS variables are resolved
        const applyInlineStyles = (sourceNode: Element, targetNode: Element) => {
            const computedStyle = window.getComputedStyle(sourceNode);

            // Loop through all computed styles and copy them
            for (const key of Array.from(computedStyle)) {
                const val = computedStyle.getPropertyValue(key);
                if (val) {
                    const priority = computedStyle.getPropertyPriority(key);
                    (targetNode as HTMLElement | SVGElement).style.setProperty(key, val, priority);
                }
            }

            // Some specific attributes that Recharts sets that need explicitly translating from CSS vars
            const presentationAttrs = ['stroke', 'fill'];
            presentationAttrs.forEach((attr) => {
                const attrValue = sourceNode.getAttribute(attr);
                if (attrValue && attrValue.includes('var(')) {
                    const match = attrValue.match(/var\(([^)]+)\)/);
                    if (match) {
                        const varName = match[1];

                        // We need to resolve the CSS variable.
                        // Checking a parent if the property isn't defined directly on the SVG element.
                        let resolvedValue = computedStyle.getPropertyValue(varName);
                        if (!resolvedValue && sourceNode.parentElement) {
                            // Find the closest ancestor that has the property defined.
                            // In this case, Recharts may use CSS vars defined in a higher scope.
                            let parent: Element | null = sourceNode;
                            while (parent && !resolvedValue) {
                                resolvedValue = window.getComputedStyle(parent).getPropertyValue(varName);
                                parent = parent.parentElement;
                            }
                        }

                        if (resolvedValue) {
                            targetNode.setAttribute(attr, resolvedValue);
                            (targetNode as HTMLElement | SVGElement).style.setProperty(
                                attr,
                                resolvedValue,
                                'important'
                            );
                        }
                    }
                }
            });
        };

        const sourceElements = Array.from(svgElement.querySelectorAll('*'));
        const targetElements = Array.from(clonedSvg.querySelectorAll('*'));

        sourceElements.forEach((sourceEl, index) => {
            applyInlineStyles(sourceEl, targetElements[index]);
        });

        applyInlineStyles(svgElement, clonedSvg);

        const svgString = new XMLSerializer().serializeToString(clonedSvg);
        const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;

            const ctx = canvas.getContext('2d');
            if (ctx) {
                // White background
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, width, height);
                ctx.drawImage(img, 0, 0);

                const dataUrl = canvas.toDataURL('image/png');
                const link = document.createElement('a');
                link.href = dataUrl;
                link.download = `${title.replace(/\s+/g, '_').toLowerCase()}_metrics.png`;
                link.click();
            }

            URL.revokeObjectURL(url);
        };
        img.src = url;
    }, [title, unwrappedGraphRef]);

    return (
        <Flex flex={1} direction={'column'} minWidth={'size-5000'}>
            <Box
                title={title}
                actions={
                    <ActionButton isQuiet onPress={handleDownload} aria-label={`Download ${title} graph`}>
                        <DownloadIcon />
                    </ActionButton>
                }
                content={
                    <View ref={graphRef} backgroundColor={'gray-50'} minHeight={'size-3800'}>
                        <LineChart
                            responsive
                            width={'100%'}
                            style={{ aspectRatio: 1.6 }}
                            data={chartData}
                            margin={{ top: 35, bottom: 45, left: 35, right: 35 }}
                        >
                            <CartesianGrid />
                            <XAxis
                                dataKey='x'
                                type='number'
                                domain={[0, 'auto']}
                                allowDecimals={false}
                                label={{ value: xAxisLabel ?? 'x', position: 'bottom', fill: '#666', offset: 20 }}
                                tickCount={X_AXIS_TICK_COUNT}
                                tickMargin={12}
                            />
                            <YAxis
                                label={{ value: yAxisLabel, angle: -90, position: 'center', dx: -38, fill: '#666' }}
                                tickCount={Y_AXIS_TICK_COUNT}
                                tickMargin={12}
                                tickFormatter={(value) =>
                                    Number.isInteger(value) ? String(value) : Number(value).toFixed(4)
                                }
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
                                labelStyle={{ color: '#333' }}
                                formatter={(value: number | string | undefined) => [
                                    Number.isInteger(Number(value)) ? Number(value) : Number(value).toFixed(4),
                                    yAxisLabel,
                                ]}
                                labelFormatter={(label: React.ReactNode) => `${xAxisLabel ?? 'x'}: ${label}`}
                            />
                            <Line
                                type='linear'
                                dataKey='y'
                                name={yAxisLabel}
                                stroke='var(--energy-blue)'
                                strokeWidth={2}
                                dot={false}
                            />
                        </LineChart>
                    </View>
                }
            />
        </Flex>
    );
};
