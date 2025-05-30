// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, useMemo } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { View } from '@geti/ui';
import { DatabaseIcon, LogsIcon, MetricsIcon, TracesIcon } from '@geti/ui/icons';
import { AnimatePresence, motion } from 'framer-motion';

import { useProductInfo } from '../../core/platform-utils/hooks/use-platform-utils.hook';
import { ANIMATION_PARAMETERS } from '../../shared/animation-parameters/animation-parameters';
import { AnalyticsDashboardCard } from './analytics-dashboard-card.component';
import { DownloadableItem, ExportServerType } from './downloadable-item.component';
import { ExportAnalyticsType } from './export-logs.component';

export const Analytics = (): JSX.Element => {
    const { router } = useApplicationServices();
    const { data } = useProductInfo();
    const isGrafanaEnabled = data?.grafanaEnabled;

    const ITEMS: ComponentProps<typeof DownloadableItem>[] = useMemo(() => {
        return [
            {
                header: ExportAnalyticsType.METRICS,
                description: 'A metric is a measurement about a service, captured at runtime.',
                url: [router.ANALYTICS.EXPORT_METRICS, router.ANALYTICS.EXPORT_SERVER_METRICS],
                icon: <MetricsIcon />,
            },
            {
                header: ExportAnalyticsType.TRACES,
                description:
                    'Traces give us the big picture of what happens when a request is made by user\n' +
                    'or an application.',
                url: [router.ANALYTICS.EXPORT_TRACES],
                icon: <TracesIcon />,
            },
            {
                header: ExportAnalyticsType.LOGS,
                description:
                    'Logs contain information about users and their interactions with\n' +
                    'the given workspace and cluster state - description of the pods, deployments.',
                url: [router.ANALYTICS.EXPORT_LOGS, router.ANALYTICS.EXPORT_SERVER_LOGS],
                icon: <LogsIcon />,
            },
            {
                header: ExportServerType.SERVER_INFO,
                description:
                    'Dump of the current state of the cluster - including details of components and additional logs.',
                url: router.ANALYTICS.EXPORT_SERVER_INFO,
                icon: <DatabaseIcon />,
            },
        ];
    }, [router]);

    return (
        <View>
            {isGrafanaEnabled && <AnalyticsDashboardCard />}
            <View marginStart={'size-75'} width={'size-6000'}>
                <AnimatePresence>
                    {ITEMS.map((item, index) => (
                        <motion.div
                            key={item.header}
                            custom={index}
                            variants={ANIMATION_PARAMETERS.ANIMATE_LIST}
                            initial={'hidden'}
                            animate={'visible'}
                        >
                            <DownloadableItem {...item} />
                        </motion.div>
                    ))}
                </AnimatePresence>
            </View>
        </View>
    );
};
