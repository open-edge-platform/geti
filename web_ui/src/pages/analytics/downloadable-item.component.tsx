// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Heading, Text, View } from '@adobe/react-spectrum';

import { idMatchingFormat } from '../../test-utils/id-utils';
import { DownloadServerInfo } from './download-server-info.component';
import { ExportAnalyticsData, ExportAnalyticsType, URLType } from './export-logs.component';

import classes from './analytics.module.scss';

export enum ExportServerType {
    SERVER_INFO = 'Server info',
}

interface DownloadableItemBaseProps {
    description: string;
    icon: JSX.Element;
}

interface DownloadableAnalyticsItemProps extends DownloadableItemBaseProps {
    header: ExportAnalyticsType.METRICS | ExportAnalyticsType.TRACES | ExportAnalyticsType.LOGS;
    url: URLType[];
}

interface DownloadableServerInfoItemProps extends DownloadableItemBaseProps {
    header: ExportServerType.SERVER_INFO;
    url: string;
}

type DownloadableItemProps = DownloadableAnalyticsItemProps | DownloadableServerInfoItemProps;

export const DownloadableItem = ({ url, icon, header, description }: DownloadableItemProps): JSX.Element => {
    return (
        <View paddingY={'size-200'}>
            <Flex gap={'size-200'} data-testid={`downloadable-item-${idMatchingFormat(header)}`}>
                <View marginTop={'size-50'}>{icon}</View>
                <View>
                    <Heading
                        level={4}
                        margin={0}
                        UNSAFE_className={classes.header}
                        id={`header-${idMatchingFormat(header)}-id`}
                    >
                        {header}
                    </Heading>
                    <Text UNSAFE_className={classes.description}>{description}</Text>
                    <View>
                        {header === ExportServerType.SERVER_INFO ? (
                            <DownloadServerInfo url={url} exportName={header.toLocaleLowerCase()} />
                        ) : (
                            <ExportAnalyticsData urls={url} exportType={header} />
                        )}
                    </View>
                </View>
            </Flex>
        </View>
    );
};
