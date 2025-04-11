// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
