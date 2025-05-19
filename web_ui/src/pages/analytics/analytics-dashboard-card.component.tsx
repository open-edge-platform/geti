// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Divider, Flex, Heading, Text, View } from '@geti/ui';
import { motion } from 'framer-motion';

import { AnalyticsIcon, ExternalLinkIcon } from '../../assets/icons';
import { useApplicationServices } from '../../core/services/application-services-provider.component';
import { ANIMATION_PARAMETERS } from '../../shared/animation-parameters/animation-parameters';
import { openNewTab } from '../../shared/utils';

import classes from './analytics.module.scss';

export const AnalyticsDashboardCard = (): JSX.Element => {
    const { router } = useApplicationServices();

    const handleOnPress = (): void => {
        openNewTab(router.ANALYTICS.DASHBOARD);
    };

    return (
        <motion.div
            variants={ANIMATION_PARAMETERS.FADE_ITEM}
            initial={'hidden'}
            animate={'visible'}
            className={classes.analyticsCard}
        >
            <View
                height={'100%'}
                width={'100%'}
                borderWidth={'thin'}
                borderColor={'gray-200'}
                data-testid={'analytics-card'}
            >
                <Flex width={'100%'} height={'100%'}>
                    <Flex flexBasis={'40%'} height={'100%'} alignItems={'center'} justifyContent={'center'}>
                        <View
                            height={'100%'}
                            width={'100%'}
                            padding={'size-300'}
                            UNSAFE_className={classes.analyticsImage}
                        >
                            <AnalyticsIcon height={'100%'} width={'100%'} />
                        </View>
                    </Flex>
                    <View flex={1} backgroundColor={'gray-75'} padding={'size-200'}>
                        <Flex height={'100%'} direction={'column'} justifyContent={'space-between'}>
                            <View flex={1}>
                                <Heading margin={0} UNSAFE_className={classes.analyticsCardHeader}>
                                    Analytics
                                </Heading>
                                <Text UNSAFE_className={classes.analyticsCardDescription}>
                                    Operational dashboards for your data. Understand your data, gain deeper insights,
                                    and make better data-driven decisions.
                                </Text>
                            </View>
                            <Divider size={'S'} UNSAFE_className={classes.analyticsDivider} marginBottom={'size-200'} />
                            <Button
                                alignSelf={'start'}
                                variant={'accent'}
                                onPress={handleOnPress}
                                id={'go-to-analytics-button-id'}
                            >
                                <Flex gap={'size-100'} alignItems={'center'}>
                                    <Text>Go to Analytics</Text>
                                    <View order={1}>
                                        <ExternalLinkIcon />
                                    </View>
                                </Flex>
                            </Button>
                        </Flex>
                    </View>
                </Flex>
            </View>
        </motion.div>
    );
};
