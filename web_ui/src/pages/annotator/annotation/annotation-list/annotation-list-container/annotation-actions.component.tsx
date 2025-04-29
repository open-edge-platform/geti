// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, View } from '@adobe/react-spectrum';

import { useIsSceneBusy } from '../../../hooks/use-annotator-scene-interaction-state.hook';
import { AnnotationsFilterChips } from '../../annotation-filter/annotation-filter-chips.component';
import { AnnotationsFilterTrigger } from '../../annotation-filter/annotation-filter-trigger.component';
import { RefreshFilterButton } from '../../annotation-filter/refresh-filters-button.component';

interface AnnotationActionsProps {
    children: ReactNode;
    isTaskChainSelectedClassification: boolean;
}

export const AnnotationActions = ({
    children,
    isTaskChainSelectedClassification,
}: AnnotationActionsProps): JSX.Element => {
    const isSceneBusy = useIsSceneBusy();

    return (
        <>
            {!isTaskChainSelectedClassification && (
                <View marginY={'size-100'}>
                    <Flex marginX={'size-100'} alignItems={'center'} gap={'size-100'}>
                        {children}
                        <View marginStart={'auto'}>
                            <AnnotationsFilterTrigger isDisabled={isSceneBusy} />
                        </View>
                    </Flex>
                </View>
            )}
            <RefreshFilterButton />
            <AnnotationsFilterChips />
        </>
    );
};
