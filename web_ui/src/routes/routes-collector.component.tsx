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

import { ReactNode, useEffect } from 'react';

import { ValueType } from '@opentelemetry/api';
import { NavigationType, useMatches, useNavigationType } from 'react-router-dom';

import { useAnalytics } from '../analytics/analytics-provider.component';
import { getMetricName } from '../analytics/metrics';

interface RoutesCollectorProps {
    children: ReactNode;
}

export const RoutesCollector = ({ children }: RoutesCollectorProps): JSX.Element => {
    const useCollectRouteChangeMetric = (): void => {
        const matches = useMatches();
        const navigationType = useNavigationType();

        const { meter } = useAnalytics();

        useEffect(() => {
            if (navigationType === NavigationType.Push || navigationType === NavigationType.Pop) {
                const routeChangeCounter = meter?.createCounter(getMetricName('pages.visits'), {
                    description: 'Metric for page visits',
                    valueType: ValueType.INT,
                });

                const match = matches.at(-1);

                if (match === undefined) {
                    return;
                }

                const { params, pathname } = match;

                // The goal of the code below is to replace params' ids with name of the route to reduce number of
                // created time series in the collector, e.g.:
                // eslint-disable-next-line max-len
                // /workspaces/646cbc76e75246605a093e1f/projects/64772694e75246605a096207/datasets/64772694e75246605a096217/annotator/image/647726bfe75246605a096235
                // /workspaces/:workspaceId/projects/:projectId/datasets/:datasetId/annotator/image/:imageId

                const genericPathname = Object.entries(params).reduce((acc, curr) => {
                    const [routeName, routeId = ''] = curr;

                    if (acc.includes(routeId)) {
                        return acc.replace(routeId, `:${routeName}`);
                    }

                    return acc;
                }, pathname);

                routeChangeCounter?.add(1, {
                    location: genericPathname,
                });
            }

            // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [matches, navigationType]);
    };

    useCollectRouteChangeMetric();

    return <>{children}</>;
};
