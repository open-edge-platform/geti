// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text, View } from '@adobe/react-spectrum';

export const ModelStatisticsNotFound = (): JSX.Element => {
    return (
        <View>
            <Text id={'models-statistics-unavailable-id'}>
                Preparing statistics... Please try again in a few minutes.
            </Text>
        </View>
    );
};
