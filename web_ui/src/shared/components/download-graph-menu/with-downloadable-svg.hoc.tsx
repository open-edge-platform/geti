// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
