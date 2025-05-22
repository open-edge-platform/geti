// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text, View } from '@geti/ui';

export const ModelStatisticsError = (): JSX.Element => {
    return (
        <View>
            <Text id={'models-statistics-unavailable-id'}>
                An unexpected error occurred during statistics preparation.
            </Text>
        </View>
    );
};
