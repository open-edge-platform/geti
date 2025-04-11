// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps, FunctionComponent, PropsWithChildren } from 'react';

import { BarChart, LineChart, PieChart, RadialBarChart, ScatterChart } from 'recharts';

import { DOWNLOADABLE_HTML_LABEL, DOWNLOADABLE_SVG_LABEL, SvgLegend } from './export-svg-utils';

export const withDownloadableHtml =
    <T,>(Component: FunctionComponent<PropsWithChildren<T>>) =>
    (props: { title: string } & ComponentProps<typeof Component>) => {
        return (
            <div
                aria-label={props.title}
                aria-valuetext={DOWNLOADABLE_HTML_LABEL}
                style={{ width: '100%', height: '100%' }}
            >
                <Component {...props} />
            </div>
        );
    };

export const withDownloadableSvg =
    (Component: typeof BarChart | typeof LineChart | typeof RadialBarChart | typeof ScatterChart | typeof PieChart) =>
    (props: { title: string; legend?: SvgLegend[] } & ComponentProps<typeof Component>) => {
        // Destructuring props here to avoid passing "title" to the svg.
        // <title> tag will show its contents if the user hover over the svg, and we dont want that
        const { title, legend, ...rest } = props;

        return (
            <Component
                {...rest}
                aria-label={title}
                aria-valuetext={DOWNLOADABLE_SVG_LABEL}
                aria-details={JSON.stringify(legend)}
            />
        );
    };
