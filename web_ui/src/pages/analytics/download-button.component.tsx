// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@adobe/react-spectrum';

import { DownloadIcon } from '../../assets/icons';
import { QuietActionButton } from '../../shared/components/quiet-button/quiet-action-button.component';
import { idMatchingFormat } from '../../test-utils/id-utils';

import classes from './analytics.module.scss';

interface DownloadButtonProps {
    exportName: string;
    handlePress?: () => void;
}

export const DownloadButton = ({ exportName, handlePress }: DownloadButtonProps): JSX.Element => {
    return (
        <QuietActionButton
            aria-label={`Download ${exportName}`}
            onPress={handlePress}
            UNSAFE_className={classes.exportAnalyticsData}
            id={`download-${idMatchingFormat(exportName)}-id`}
        >
            <Flex alignItems={'center'} gap={'size-100'} width={'100%'}>
                <Text order={-1}>Download</Text>
                <View>
                    <DownloadIcon />
                </View>
            </Flex>
        </QuietActionButton>
    );
};
